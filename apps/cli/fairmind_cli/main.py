"""fairmind: gate, test and systems.

    fairmind gate --system <id>                 exit 0 go, 2 conditional go, 1 no go
    fairmind gate --system <id> --require-approval   also exit 1 unless the release decision is approved
    fairmind test --system <id> --file p.csv \
        --outcome repaid --attributes gender,region [--prediction approved] [--score score]
    fairmind monitor --system <id> --file decisions.csv --attributes gender [--prediction approved] [--score score]
    fairmind systems
    fairmind verify pack.json                   offline: recompute the pack hash and chain heads; exit 0 intact, 1 not

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
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence

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
        return EXIT_GO if args.allow_conditional else EXIT_CONDITIONAL
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


def cmd_verify(args: argparse.Namespace, factory: ClientFactory, out: Callable[[str], None]) -> int:
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

    verify = sub.add_parser("verify", help="verify a downloaded inspection pack offline (no network); exit 0 intact, 1 not", description=CANONICAL_FORM)
    verify.add_argument("pack", help="pack JSON downloaded from FairMind or an auditor link")
    verify.add_argument("--json", action="store_true", help="print the result as JSON")
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
