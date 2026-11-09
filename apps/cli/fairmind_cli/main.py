"""fairmind: gate, test and systems.

    fairmind gate --system <id>                 exit 0 go, 2 conditional go, 1 no go
    fairmind gate --system <id> --require-approval   exit 1 unless the release decision is approved; approved, a conditional go exits 0
    fairmind test --system <id> --file p.csv \
        --outcome repaid --attributes gender,region [--prediction approved] [--score score]
    fairmind monitor --system <id> --file decisions.csv --attributes gender [--prediction approved] [--score score]
    fairmind systems
    fairmind verify pack.json                   offline: recompute the pack hash and chain heads; exit 0 intact, 1 not
    fairmind verify "<share link>" [--api URL]  fetch the pack behind an auditor link, then verify it locally
    fairmind clause-map --system <id> [--frameworks EUAIA,ISO42001]   the gate read per framework clause
    fairmind system get <id> | create --name N [--risk-tier T --stage S --workspace W --owner O]
    fairmind pack create|list|show|download|share|revoke   inspection packs
    fairmind finding add|list                   risk findings
    fairmind remediation add|list|update        remediation tasks
    fairmind approval request|status|decide     release decisions
    fairmind report generate|list               audit report snapshots
    fairmind eval list|show|run|result          evaluation catalogue and runs

Configuration comes from flags or the environment: FAIRMIND_API_URL (default
http://localhost:8010) and FAIRMIND_API_KEY, a key minted at POST /api/v1/auth/api-keys.
Exit code 3 means the command itself failed (network, auth, bad input).
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence
from urllib.parse import parse_qs, urlparse

import httpx

from . import __version__

GOV = "/api/v1/ai-governance"
EXIT_GO, EXIT_NO_GO, EXIT_CONDITIONAL, EXIT_ERROR = 0, 1, 2, 3

ClientFactory = Callable[[str, Dict[str, str]], httpx.Client]


class CliError(Exception):
    """Reported to stderr with exit code 3."""


def _default_client(base_url: str, headers: Dict[str, str]) -> httpx.Client:
    return httpx.Client(base_url=base_url, headers=headers, timeout=httpx.Timeout(180.0, connect=10.0))


def _client(args: argparse.Namespace, factory: ClientFactory) -> httpx.Client:
    base_url = (args.api or os.environ.get("FAIRMIND_API_URL") or "http://localhost:8010").rstrip("/")
    key = args.api_key or os.environ.get("FAIRMIND_API_KEY") or ""
    headers = {"Accept": "application/json", "User-Agent": f"fairmind-cli/{__version__}"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return factory(base_url, headers)


def _call(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = client.request(method, path, **kwargs)
    except httpx.HTTPError as exc:
        raise CliError(f"Could not reach FairMind at {client.base_url}: {exc}") from exc
    if response.status_code == 401:
        raise CliError("Not signed in. Set FAIRMIND_API_KEY to a key from POST /api/v1/auth/api-keys.")
    if response.status_code == 404:
        raise CliError(f"Not found: {path}. Check the system id and that your key belongs to its organisation.")
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail") or response.json().get("message") or response.text
        except ValueError:
            detail = response.text
        raise CliError(f"{method} {path} failed with {response.status_code}: {detail}")
    try:
        return response.json()
    except ValueError as exc:
        raise CliError(f"{method} {path} returned something that is not JSON") from exc


# ---------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------

VERDICT_WORD = {"go": "GO", "conditional_go": "CONDITIONAL GO", "no_go": "NO GO"}
STATE_MARK = {"proven": "+", "attested": "~", "open": "-"}
APPROVAL_WORD = {"not_requested": "not requested", "pending": "pending", "approved": "approved", "rejected": "rejected"}


def render_gate(gate: Dict[str, Any]) -> str:
    lines = [
        f"{VERDICT_WORD.get(gate['verdict'], gate['verdict'])}  confidence {gate['confidence']:.2f} ({gate['band']})  "
        f"{gate['proven']} proven, {gate['attested']} attested, {gate['open']} open",
        "",
    ]
    for check in gate.get("checks", []):
        conf = f" {check['confidence']:.2f}" if check.get("confidence") else ""
        lines.append(f"  {STATE_MARK.get(check['state'], '?')} {check['label']:<22} {check['state']}{conf}")
    if "approvalStatus" in gate:
        lines.append(f"    {'Release decision':<22} {APPROVAL_WORD.get(gate['approvalStatus'], gate['approvalStatus'])}")
    if gate.get("reasons"):
        lines.append("")
        lines.extend(f"  {reason}" for reason in gate["reasons"])
    return "\n".join(lines)


def cmd_gate(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        gate = _call(client, "GET", f"{GOV}/systems/{args.system}/gate")
    out(json.dumps(gate, indent=2) if args.json else render_gate(gate))
    if args.require_approval and gate.get("approvalStatus") != "approved":
        status = APPROVAL_WORD.get(gate.get("approvalStatus"), "not reported by this server")
        print(f"fairmind: --require-approval: the release decision is {status}", file=sys.stderr)
        return EXIT_NO_GO
    verdict = gate.get("verdict")
    if verdict == "go":
        return EXIT_GO
    if verdict == "conditional_go":
        # Past --require-approval the decision is approved, and approving a conditional go records the accepted conditions.
        return EXIT_GO if args.allow_conditional or args.require_approval else EXIT_CONDITIONAL
    return EXIT_NO_GO


# ---------------------------------------------------------------------------
# test
# ---------------------------------------------------------------------------

def render_run(run: Dict[str, Any]) -> str:
    result = run["result"]
    lines = [
        f"{'All checks within thresholds' if result['all_checks_pass'] else 'At least one check outside thresholds'}  "
        f"{result['rows']} rows  evidence confidence {result['evidence_confidence']:.2f} (measured)  evidence {run['evidenceId']}",
        "",
        f"  {'attribute':<14}{'impact ratio':>13}{'eq. opp. gap':>14}{'eq. odds gap':>14}{'calibration':>13}",
    ]
    for attr in result["attributes"]:
        checks = attr["checks"]
        def cell(value: Optional[float], ok: Optional[bool], width: int) -> str:
            if value is None:
                return f"{'n/a':>{width}}"
            mark = "" if ok else "!"
            return f"{value:.3f}{mark}".rjust(width)
        cal = attr.get("calibration")
        lines.append(
            f"  {attr['attribute']:<14}"
            + cell(attr["disparate_impact_ratio"], checks.get("disparate_impact"), 13)
            + cell(attr["equal_opportunity"]["value"], checks.get("equal_opportunity"), 14)
            + cell(attr["equalized_odds"]["value"], checks.get("equalized_odds"), 14)
            + cell(cal["value"] if cal else None, checks.get("calibration"), 13)
        )
        if attr.get("small_groups"):
            lines.append(f"  {'':<14}small groups: {', '.join(attr['small_groups'])}")
    lines.append("")
    lines.append("  ! marks a check outside its threshold (impact ratio below 0.80, gap above 0.05)")
    lines.append("")
    lines.append(render_gate(run["gate"]))
    return "\n".join(lines)


def cmd_test(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    path = Path(args.file)
    if not path.is_file():
        raise CliError(f"No such file: {path}")
    data = {"outcome": args.outcome, "attributes": args.attributes}
    if args.prediction:
        data["prediction"] = args.prediction
    if args.score:
        data["score"] = args.score
    if args.favorable_label:
        data["favorable_label"] = args.favorable_label
    if not args.prediction and not args.score:
        raise CliError("Give --prediction (a 0/1 column) or --score (a 0 to 1 column)")
    with _client(args, factory) as client, path.open("rb") as handle:
        run = _call(client, "POST", f"{GOV}/systems/{args.system}/fairness-runs", data=data, files={"file": (path.name, handle, "text/csv")})
    out(json.dumps(run, indent=2) if args.json else render_run(run))
    if args.gate:
        verdict = run["gate"]["verdict"]
        if verdict == "go":
            return EXIT_GO
        if verdict == "conditional_go":
            return EXIT_GO if args.allow_conditional else EXIT_CONDITIONAL
        return EXIT_NO_GO
    return EXIT_GO if run["result"]["all_checks_pass"] else EXIT_NO_GO


# ---------------------------------------------------------------------------
# monitor
# ---------------------------------------------------------------------------

def render_monitoring(run: Dict[str, Any]) -> str:
    result = run["result"]
    base = result["baseline"]
    lines = [
        f"{'Stable against the baseline' if result['all_checks_pass'] else 'Drift or disparity outside thresholds'}  "
        f"{result['rows']} rows  overall score PSI {('%.3f' % result['overall_psi']) if result.get('overall_psi') is not None else 'n/a'}  "
        f"baseline {'present' if base.get('present') else 'none (run a fairness test first)'}  evidence {run['evidenceId']}",
        "",
        f"  {'attribute':<14}{'max rate drift':>15}{'impact ratio':>13}{'worst PSI':>11}",
    ]
    for attr in result["attributes"]:
        checks = attr["checks"]
        def cell(value: Optional[float], ok: Optional[bool], width: int) -> str:
            if value is None:
                return f"{'n/a':>{width}}"
            return f"{value:.3f}{'' if ok in (None, True) else '!'}".rjust(width)
        lines.append(f"  {attr['attribute']:<14}" + cell(attr.get("max_rate_drift"), checks.get("selection_rate_stable"), 15) + cell(attr["disparate_impact_ratio"], checks.get("disparate_impact"), 13) + cell(attr.get("worst_psi"), checks.get("score_stable"), 11))
    lines += ["", "  ! marks a check outside its threshold (rate drift above 0.05, impact ratio below 0.80, PSI at or above 0.10)", "", render_gate(run["gate"])]
    return "\n".join(lines)


def cmd_monitor(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    path = Path(args.file)
    if not path.is_file():
        raise CliError(f"No such file: {path}")
    if not args.prediction and not args.score:
        raise CliError("Give --prediction (a 0/1 column) or --score (a 0 to 1 column)")
    data = {"attributes": args.attributes}
    if args.prediction:
        data["prediction"] = args.prediction
    if args.score:
        data["score"] = args.score
    with _client(args, factory) as client, path.open("rb") as handle:
        run = _call(client, "POST", f"{GOV}/systems/{args.system}/monitoring-runs", data=data, files={"file": (path.name, handle, "text/csv")})
    out(json.dumps(run, indent=2) if args.json else render_monitoring(run))
    return EXIT_GO if run["result"]["all_checks_pass"] else EXIT_NO_GO


# ---------------------------------------------------------------------------
# systems
# ---------------------------------------------------------------------------

def cmd_systems(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        systems = _call(client, "GET", f"{GOV}/systems")
    if args.json:
        out(json.dumps(systems, indent=2))
        return EXIT_GO
    if not systems:
        out("No systems in your organisation yet. Connect a source or register one in FairMind.")
        return EXIT_GO
    width = max(len(s.get("name", "")) for s in systems)
    out(f"  {'name':<{width}}  {'tier':<9}{'stage':<10}id")
    for s in systems:
        out(f"  {s.get('name', ''):<{width}}  {s.get('riskTier', ''):<9}{s.get('lifecycleStage', ''):<10}{s.get('id', '')}")
    return EXIT_GO


# ---------------------------------------------------------------------------
# verify (offline)
# ---------------------------------------------------------------------------

CANONICAL_FORM = (
    'Canonical form: sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()). '
    'Chain head per system: h = sha256("fairmind-evidence-chain-v1"); for each evidence entry in order, '
    'h = sha256(f"{h}:{entry.hash}"). The file is {"manifest": {...}, "manifestHash": "..."}.'
)


def _chain_head(entries: Sequence[Dict[str, Any]]) -> str:
    head = hashlib.sha256(b"fairmind-evidence-chain-v1").hexdigest()
    for entry in entries:
        head = hashlib.sha256(f"{head}:{entry['hash']}".encode()).hexdigest()
    return head


def verify_pack(document: Dict[str, Any]) -> Dict[str, Any]:
    """Pure check of a downloaded pack; no network."""
    manifest, expected = document.get("manifest"), document.get("manifestHash")
    if not isinstance(manifest, dict) or not isinstance(expected, str):
        raise CliError('Not an inspection pack: expected {"manifest": {...}, "manifestHash": "..."}')
    actual = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    systems = []
    for item in manifest.get("systems", []):
        try:
            recomputed = _chain_head(item.get("evidence", []))
        except (KeyError, TypeError) as exc:
            raise CliError(f"Malformed evidence entry: {exc!r}") from exc
        system = item.get("system") or {}
        systems.append({"name": system.get("name") or system.get("id"), "evidence": len(item.get("evidence", [])), "intact": hmac.compare_digest(str(item.get("chainHead")), recomputed)})
    hash_ok = hmac.compare_digest(expected, actual)
    return {"title": manifest.get("title"), "hashOk": hash_ok, "expected": expected, "actual": actual, "systems": systems, "intact": hash_ok and all(s["intact"] for s in systems)}


def _fetch_shared(link: str, args: argparse.Namespace, factory: ClientFactory) -> Dict[str, Any]:
    parts = urlparse(link)
    token = (parse_qs(parts.query).get("t") or [""])[0]
    pack_id = parts.path.rstrip("/").rsplit("/", 1)[-1]
    if not token or not pack_id:
        raise CliError("Not a share link: expected .../verify/<pack id>?t=<token>")
    with _client(args, factory) as client:
        shared = _call(client, "GET", f"/api/v1/public/packs/{pack_id}", params={"t": token})
    return {"manifest": shared["manifest"], "manifestHash": shared["manifestHash"]}


def cmd_verify(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    if args.pack.startswith(("http://", "https://")):
        document = _fetch_shared(args.pack, args, factory)
    else:
        path = Path(args.pack)
        if not path.is_file():
            raise CliError(f"No such file: {path}")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise CliError(f"{path} is not valid JSON: {exc}") from exc
    result = verify_pack(document)
    if args.json:
        out(json.dumps(result, indent=2))
    else:
        out(f"{result['title']}")
        out(f"  manifest hash  {'ok' if result['hashOk'] else 'MISMATCH'}  {result['actual']}")
        if not result["hashOk"]:
            out(f"  recorded       {result['expected']}")
        for s in result["systems"]:
            out(f"  {'ok' if s['intact'] else 'BROKEN':<9}{s['name']}  {s['evidence']} evidence records, chain head {'matches' if s['intact'] else 'does not match'}")
        out("")
        out("Pack intact" if result["intact"] else "Pack does NOT verify: it was changed after it was built")
    return EXIT_GO if result["intact"] else EXIT_NO_GO


# ---------------------------------------------------------------------------
# packs, findings, remediation, approvals, reports, evaluations
# ---------------------------------------------------------------------------

def _show(out: Callable[[str], None], args: argparse.Namespace, data: Any, summary: Callable[[Any], str]) -> int:
    out(json.dumps(data, indent=2) if args.json else summary(data))
    return EXIT_GO


def _org(client: httpx.Client) -> str:
    org = os.environ.get("FAIRMIND_ORG_ID")
    if org:
        return org
    orgs = _call(client, "GET", "/api/v1/organizations").get("organizations") or []
    if not orgs:
        raise CliError("This key belongs to no organisation")
    return orgs[0]["id"]


def _csv_list(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def cmd_pack(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        pid = f"{GOV}/packs/{getattr(args, 'id', '')}"
        if args.action == "create":
            pack = _call(client, "POST", f"{GOV}/packs", json={"title": args.title, "frameworks": _csv_list(args.frameworks), "system_ids": _csv_list(args.systems)})
            return _show(out, args, pack, lambda p: f"Pack {p['id']}  {p['title']}\n  hash {p['manifestHash']}")
        if args.action == "list":
            return _show(out, args, _call(client, "GET", f"{GOV}/packs"), lambda ps: "\n".join(f"{p['id']}  {p['title']}  {'shared' if p['share']['shared'] else 'private'}" for p in ps) or "No packs yet.")
        if args.action == "show":
            return _show(out, args, _call(client, "GET", pid), lambda p: f"{p['id']}  {p['title']}\n  hash {p['manifestHash']}  frameworks {', '.join(p['frameworks'])}")
        if args.action == "download":
            document = _call(client, "GET", f"{pid}/download")
            target = Path(args.output or f"pack-{args.id}.json")
            target.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
            out(f"Saved {target}; check it with: fairmind verify {target}")
            return EXIT_GO
        if args.action == "share":
            return _show(out, args, _call(client, "POST", f"{pid}/share"), lambda s: f"Auditor token (shown once): {s['token']}\n  expires {s['expiresAt']}\n  link: <FairMind site>/verify/{s['packId']}?t={s['token']}")
        return _show(out, args, _call(client, "DELETE", f"{pid}/share"), lambda s: f"Share link for {s['packId']} revoked")


def cmd_finding(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        if args.action == "add":
            body = {"systemId": args.system, "riskType": args.type, "severity": args.severity, "description": args.description}
            return _show(out, args, _call(client, "POST", f"{GOV}/risks/assess", json=body), lambda f: f"Finding {f['id']}: {f['title']}, {f['severity']}, {f['status']}")
        found = _call(client, "GET", f"{GOV}/dashboard/risk", params={"system_id": args.system} if args.system else {})
        return _show(out, args, found, lambda f: "\n".join(f"{r['id']}  {r['severity']:<9}{r['status']:<9}{r['title']}" for r in f["risks"]) or "No findings recorded.")


def cmd_remediation(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        if args.action == "add":
            body: Dict[str, Any] = {
                "system_id": args.system, "title": args.title, "description": args.description, "source_type": "risk",
                "source_id": args.finding or args.system, "linked_risk_ids": [args.finding] if args.finding else [], "priority": args.priority,
            }
            if args.owner:
                body["owner"] = args.owner
            return _show(out, args, _call(client, "POST", f"{GOV}/remediation", json=body), lambda t: f"Task {t['id']}: {t['title']}, {t['priority']}, {t['status']}")
        if args.action == "list":
            return _show(out, args, _call(client, "GET", f"{GOV}/remediation", params={"system_id": args.system}), lambda r: "\n".join(f"{t['id']}  {t['priority']:<9}{t['status']:<17}{t['title']}" for t in r["tasks"]) or "No tasks.")
        body = {k: v for k, v in (("status", args.status), ("notes", args.notes)) if v is not None}
        return _show(out, args, _call(client, "PATCH", f"{GOV}/remediation/{args.task}", json=body), lambda t: f"Task {t['id']}: {t['status']}")


def cmd_approval(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    summary = lambda s: f"Release decision: {s['request']['status'] if s['request'] else 'not requested'}" + (f"  request {s['request']['id']}" if s["request"] else "")  # noqa: E731
    with _client(args, factory) as client:
        if args.action == "request":
            return _show(out, args, _call(client, "POST", f"{GOV}/approval/system/{args.system}/request", json={}), summary)
        if args.action == "status":
            return _show(out, args, _call(client, "GET", f"{GOV}/approval/system/{args.system}"), summary)
        body = {"decision": args.decision, "notes": args.notes or ""}
        return _show(out, args, _call(client, "POST", f"{GOV}/approval-requests/{args.request}/decision", json=body), lambda d: f"Decision recorded: {args.decision}")


def cmd_report(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        if args.action == "generate":
            body: Dict[str, Any] = {"system_id": args.system, "report_type": args.type}
            if args.title:
                body["title"] = args.title
            if args.frameworks:
                body["frameworks"] = _csv_list(args.frameworks)
            return _show(out, args, _call(client, "POST", f"{GOV}/reports/generate", json=body), lambda r: f"Report {r['id']}: {r['title']}")
        params = {"system_id": args.system, **({"report_type": args.type} if args.type else {})}
        return _show(out, args, _call(client, "GET", f"{GOV}/reports", params=params), lambda rs: "\n".join(f"{r['id']}  {r['reportType']:<11}{r['createdAt']}  {r['title']}" for r in rs) or "No reports.")


def cmd_clause_map(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        cmap = _call(client, "GET", f"{GOV}/systems/{args.system}/clause-map")
    if args.frameworks:
        wanted = {f.upper() for f in _csv_list(args.frameworks)}
        cmap["frameworks"] = [f for f in cmap["frameworks"] if f["key"].upper() in wanted]

    def text(c: Dict[str, Any]) -> str:
        lines = [f"Gate {VERDICT_WORD.get(c['verdict'], c['verdict'])}, confidence {c['confidence']:.2f}"]
        for fw in c["frameworks"]:
            n = fw["counts"]
            lines.append(f"{fw['name']} ({fw['key']}): {n['proven']} proven, {n['attested']} attested, {n['open']} open of {n['total']} clauses")
            open_clauses = [cl["control"] for cl in fw["clauses"] if cl["state"] == "open"]
            if open_clauses:
                lines.append(f"  open: {', '.join(open_clauses)}")
        return "\n".join(lines)

    return _show(out, args, cmap, text)


def cmd_system(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    line = lambda s: f"{s.get('name', '')}  tier {s.get('riskTier', '')}  stage {s.get('lifecycleStage', '')}  id {s.get('id', '')}"  # noqa: E731
    with _client(args, factory) as client:
        if args.action == "get":
            return _show(out, args, _call(client, "GET", f"{GOV}/systems/{args.id}"), line)
        workspace = args.workspace
        if not workspace:  # the organisation's first workspace, else a new one named "Default"
            existing = _call(client, "GET", f"{GOV}/workspaces")
            workspace = existing[-1]["id"] if existing else _call(client, "POST", f"{GOV}/workspaces", json={"name": "Default"})["id"]
        body: Dict[str, Any] = {"workspace_id": workspace, "name": args.name, "risk_tier": args.risk_tier, "lifecycle_stage": args.stage, "metadata": {}}
        if args.owner:
            body["owner"] = args.owner
        return _show(out, args, _call(client, "POST", f"{GOV}/systems", json=body), line)


def _render_eval_run(run: Dict[str, Any]) -> str:
    lines = [f"{run.get('evaluationId')}: {str(run.get('status', '')).upper()}  evidence {run.get('id')}"]
    if run.get("summary"):
        lines.append(f"  {run['summary']}")
    lines += [f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}" for k, v in (run.get("metrics") or {}).items()]
    return "\n".join(lines)


def cmd_eval(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
    with _client(args, factory) as client:
        packs = lambda path, **kw: _call(client, kw.pop("method", "GET"), f"/api/v1/packs{path}", **{**kw, "params": {**kw.get("params", {}), "org_id": _org(client)}})  # noqa: E731
        if args.action == "list":
            params = {k: v for k, v in (("q", args.query), ("pillar", args.pillar)) if v}
            return _show(out, args, packs("/evaluations", params=params), lambda es: "\n".join(f"{e['id']}  {'runnable' if e.get('runnable') else 'evidence only'}  {e['name']}" for e in es) or "No evaluation matches.")
        if args.action == "show":
            return _show(out, args, packs(f"/evaluations/{args.id}/engine"), lambda e: "\n".join([f"method: {e['method']}"] + [f"  file {s['name']}{'' if s['required'] else ' (optional)'}: {s['help']}" for s in e["slots"]] + [f"  param {p['name']}{' (required)' if p['required'] else ''}: {p['help']}" for p in e["params"]]))
        if args.action == "result":
            return _show(out, args, packs(f"/evaluation-runs/{args.id}"), _render_eval_run)
        files, params = {}, {}
        for item in args.file or []:
            slot, _, path = item.partition("=")
            if not path or not Path(path).is_file():
                raise CliError(f"--file expects slot=path to an existing file, got {item!r}")
            files[slot] = Path(path)
        for item in args.param or []:
            key, _, value = item.partition("=")
            try:
                params[key] = json.loads(value)
            except ValueError:
                params[key] = value
        data = {"system_id": args.system, "params": json.dumps(params), "source": "connection" if args.use_connection else "upload"}
        if args.live:
            data["mode"] = "live"
        handles = {slot: (p.name, p.open("rb")) for slot, p in files.items()}
        try:
            result = packs(f"/evaluations/{args.id}/runs", method="POST", data=data, files=handles or None)
        finally:
            for _, handle in handles.values():
                handle.close()
        job = result.get("job") if isinstance(result, dict) else None
        if job:
            deadline = time.monotonic() + args.timeout
            while job["status"] not in ("done", "failed"):
                if time.monotonic() > deadline:
                    raise CliError(f"Evaluation job {job['id']} is still running after {args.timeout:.0f}s; check it later")
                time.sleep(3)
                job = packs(f"/evaluation-jobs/{job['id']}")
            if job["status"] == "failed":
                raise CliError(f"Evaluation {args.id} failed: {job.get('error') or 'no reason given'}")
            result = packs(f"/evaluation-runs/{job['evidenceId']}")
        _show(out, args, result, _render_eval_run)
        return EXIT_GO if result.get("status") == "passed" else EXIT_NO_GO

# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fairmind", description="FairMind release gate and fairness tests.")
    parser.add_argument("--version", action="version", version=f"fairmind-cli {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api", help="FairMind API base URL (default: FAIRMIND_API_URL or http://localhost:8010)")
    common.add_argument("--api-key", help="API key (default: FAIRMIND_API_KEY)")
    common.add_argument("--json", action="store_true", help="print the raw response")

    sub = parser.add_subparsers(dest="command", required=True)

    gate = sub.add_parser("gate", parents=[common], help="read the release gate; exit 0 go, 2 conditional, 1 no go")
    gate.add_argument("--system", required=True, help="AI system id")
    gate.add_argument("--allow-conditional", action="store_true", help="exit 0 on a conditional go")
    gate.add_argument("--require-approval", action="store_true", help="exit 1 unless the release decision is approved (with or without conditions)")
    gate.set_defaults(func=cmd_gate)

    test = sub.add_parser("test", parents=[common], help="run a fairness test from a predictions CSV and store it as evidence")
    test.add_argument("--system", required=True, help="AI system id")
    test.add_argument("--file", required=True, help="CSV with one row per decision")
    test.add_argument("--outcome", required=True, help="column with what happened (0/1)")
    test.add_argument("--attributes", required=True, help="comma-separated protected attribute columns")
    test.add_argument("--prediction", help="column with the model's decision (0/1)")
    test.add_argument("--score", help="column with the model's score (0 to 1)")
    test.add_argument("--favorable-label", help="value that counts as the favourable outcome when columns are not 0/1")
    test.add_argument("--gate", action="store_true", help="exit by the release gate's verdict instead of the test's checks")
    test.add_argument("--allow-conditional", action="store_true", help="with --gate: exit 0 on a conditional go")
    test.set_defaults(func=cmd_test)

    monitor = sub.add_parser("monitor", parents=[common], help="record a monitoring snapshot from recent decisions; exit 1 on drift or disparity")
    monitor.add_argument("--system", required=True, help="AI system id")
    monitor.add_argument("--file", required=True, help="CSV of recent decisions")
    monitor.add_argument("--attributes", required=True, help="comma-separated protected attribute columns")
    monitor.add_argument("--prediction", help="column with the model's decision (0/1)")
    monitor.add_argument("--score", help="column with the model's score (0 to 1)")
    monitor.set_defaults(func=cmd_monitor)

    systems = sub.add_parser("systems", parents=[common], help="list the AI systems your key can see")
    systems.set_defaults(func=cmd_systems)

    def group(name: str, help: str, actions: Dict[str, str], func: Callable[..., int]) -> Dict[str, argparse.ArgumentParser]:
        parent = sub.add_parser(name, help=help)
        inner = parent.add_subparsers(dest="action", required=True)
        made = {}
        for action, text in actions.items():
            made[action] = inner.add_parser(action, parents=[common], help=text)
            made[action].set_defaults(func=func)
        return made

    cmap = sub.add_parser("clause-map", parents=[common], help="the release gate read per framework clause")
    cmap.add_argument("--system", required=True)
    cmap.add_argument("--frameworks", help="comma-separated catalogue keys, e.g. EUAIA,ISO42001")
    cmap.set_defaults(func=cmd_clause_map)

    sysg = group("system", "one AI system", {"get": "show a system", "create": "register a system"}, cmd_system)
    sysg["get"].add_argument("id", help="system id")
    sysg["create"].add_argument("--name", required=True)
    sysg["create"].add_argument("--risk-tier", default="medium", choices=["low", "medium", "high", "critical"])
    sysg["create"].add_argument("--stage", default="assess", choices=["onboard", "assess", "govern", "remediate", "operate"])
    sysg["create"].add_argument("--workspace", help="workspace id (default: the organisation's first, or a new Default)")
    sysg["create"].add_argument("--owner")

    pack = group("pack", "inspection packs", {"create": "build a pack", "list": "list packs", "show": "pack summary", "download": "save pack.json", "share": "mint an auditor link token", "revoke": "revoke the link"}, cmd_pack)
    pack["create"].add_argument("--title", required=True)
    pack["create"].add_argument("--frameworks", required=True, help="comma-separated catalogue keys, e.g. EUAIA,ISO42001")
    pack["create"].add_argument("--systems", required=True, help="comma-separated system ids")
    for a in ("show", "download", "share", "revoke"):
        pack[a].add_argument("id", help="pack id")
    pack["download"].add_argument("-o", "--output", help="file to write (default pack-<id>.json)")

    finding = group("finding", "risk findings", {"add": "record a finding", "list": "list findings"}, cmd_finding)
    finding["add"].add_argument("--system", required=True)
    finding["add"].add_argument("--type", required=True, help="risk type, e.g. bias or privacy")
    finding["add"].add_argument("--severity", required=True, choices=["low", "medium", "high", "critical"])
    finding["add"].add_argument("--description", required=True)
    finding["list"].add_argument("--system", help="limit to one system")

    rem = group("remediation", "remediation tasks", {"add": "open a task", "list": "list a system's tasks", "update": "change status or notes"}, cmd_remediation)
    rem["add"].add_argument("--system", required=True)
    rem["add"].add_argument("--title", required=True)
    rem["add"].add_argument("--description", required=True)
    rem["add"].add_argument("--finding", help="finding id this task fixes")
    rem["add"].add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"])
    rem["add"].add_argument("--owner")
    rem["list"].add_argument("--system", required=True)
    rem["update"].add_argument("task", help="task id")
    rem["update"].add_argument("--status", choices=["open", "in_progress", "blocked", "ready_for_retest", "resolved", "closed"])
    rem["update"].add_argument("--notes")

    appr = group("approval", "release decisions", {"request": "ask for a decision", "status": "read the latest decision", "decide": "approve or reject a request"}, cmd_approval)
    for a in ("request", "status"):
        appr[a].add_argument("--system", required=True)
    appr["decide"].add_argument("request", help="approval request id")
    appr["decide"].add_argument("--decision", required=True, choices=["approved", "rejected"])
    appr["decide"].add_argument("--notes")

    rep = group("report", "audit report snapshots", {"generate": "generate and store a snapshot", "list": "list stored snapshots"}, cmd_report)
    rep["generate"].add_argument("--system", required=True)
    rep["generate"].add_argument("--type", required=True, choices=["compliance", "bias", "governance"])
    rep["generate"].add_argument("--title")
    rep["generate"].add_argument("--frameworks", help="comma-separated")
    rep["list"].add_argument("--system", required=True)
    rep["list"].add_argument("--type", choices=["compliance", "bias", "governance"])

    ev = group("eval", "evaluation catalogue and runs", {"list": "search the catalogue", "show": "files and params an evaluation takes", "run": "run an evaluation and wait for the result", "result": "read a stored run"}, cmd_eval)
    ev["list"].add_argument("-q", "--query")
    ev["list"].add_argument("--pillar")
    ev["show"].add_argument("id", help="evaluation id")
    ev["result"].add_argument("id", help="run (evidence) id")
    ev["run"].add_argument("id", help="evaluation id")
    ev["run"].add_argument("--system", required=True)
    ev["run"].add_argument("--file", action="append", help="slot=path, repeatable")
    ev["run"].add_argument("--param", action="append", help="name=value, repeatable")
    ev["run"].add_argument("--live", action="store_true", help="behaviour test against the system's connected endpoint")
    ev["run"].add_argument("--use-connection", action="store_true", help="read the organisation's agent platform instead of files")
    ev["run"].add_argument("--timeout", type=float, default=900.0)

    verify = sub.add_parser("verify", parents=[common], help="verify an inspection pack (a downloaded pack.json is checked with no network; a share link is fetched first); exit 0 intact, 1 not", description=CANONICAL_FORM)
    verify.add_argument("pack", help="pack JSON downloaded from FairMind, or an auditor share link (.../verify/<id>?t=<token>)")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: Optional[Sequence[str]] = None, *, client_factory: ClientFactory = _default_client, out: Callable[[str], None] = print) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args, client_factory, out))
    except CliError as exc:
        print(f"fairmind: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
