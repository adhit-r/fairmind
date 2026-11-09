"""HTTP client for the FairMind API. Mirrors the conventions of the fairmind CLI."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

import httpx

from . import __version__
from .types import Attestation, AttestableCheck, ClauseMap, FairnessRun, Gate, MonitoringRun, System

GOV = "/api/v1/ai-governance"
PACKS = "/api/v1/packs"
DEFAULT_API_URL = "http://localhost:8010"

# legacy framework ids -> catalogue keys, as accepted by the report request
_FRAMEWORK_ALIASES = {"eu_ai_act": "EUAIA", "iso_42001": "ISO42001", "nist_ai_rmf": "NISTRMF", "india_ai": "INDAI"}

PathLike = Union[str, "os.PathLike[str]"]


class FairMindError(Exception):
    """A failed call. `status_code` is None when the server could not be reached."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}" if self.status_code else self.message


def _split(value: Union[str, Sequence[str]]) -> str:
    return value if isinstance(value, str) else ",".join(value)


def _chain_head(entries: Sequence[Dict[str, Any]]) -> str:
    head = hashlib.sha256(b"fairmind-evidence-chain-v1").hexdigest()
    for entry in entries:
        head = hashlib.sha256(f"{head}:{entry['hash']}".encode()).hexdigest()
    return head


def verify_pack(document: Dict[str, Any]) -> Dict[str, Any]:
    """Check an inspection pack offline: `{"manifest": {...}, "manifestHash": "..."}` as downloaded or shared.

    Recomputes the SHA-256 of the canonical manifest and each system's evidence chain head. `intact` is true only
    when the manifest hash and every chain head match. Pure: no network, no key.
    """
    manifest, expected = document.get("manifest"), document.get("manifestHash")
    if not isinstance(manifest, dict) or not isinstance(expected, str):
        raise FairMindError('Not an inspection pack: expected {"manifest": {...}, "manifestHash": "..."}')
    actual = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    systems = []
    for item in manifest.get("systems", []):
        try:
            recomputed = _chain_head(item.get("evidence", []))
        except (KeyError, TypeError) as exc:
            raise FairMindError(f"Malformed evidence entry: {exc!r}") from exc
        system = item.get("system") or {}
        systems.append({"name": system.get("name") or system.get("id"), "evidence": len(item.get("evidence", [])), "intact": hmac.compare_digest(str(item.get("chainHead")), recomputed)})
    hash_ok = hmac.compare_digest(expected, actual)
    return {"title": manifest.get("title"), "hashOk": hash_ok, "expected": expected, "actual": actual, "systems": systems, "intact": hash_ok and all(s["intact"] for s in systems)}


class FairMind:
    """`FairMind(api_url=None, api_key=None)`; FAIRMIND_API_URL and FAIRMIND_API_KEY are read when omitted."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout: Union[float, httpx.Timeout] = httpx.Timeout(180.0, connect=10.0),
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.api_url = (api_url or os.environ.get("FAIRMIND_API_URL") or DEFAULT_API_URL).rstrip("/")
        key = api_key or os.environ.get("FAIRMIND_API_KEY") or ""
        headers = {"Accept": "application/json", "User-Agent": f"fairmind-sdk/{__version__}"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        self._http = httpx.Client(base_url=self.api_url, headers=headers, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "FairMind":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- transport -----------------------------------------------------------

    def _call(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise FairMindError(f"Could not reach FairMind at {self.api_url}: {exc}") from exc
        code = response.status_code
        if code == 401:
            raise FairMindError("Not signed in. Set FAIRMIND_API_KEY to a key from POST /api/v1/auth/api-keys.", code)
        if code >= 400:
            try:
                body = response.json()
                detail = body.get("detail") or body.get("message") or response.text
            except (ValueError, AttributeError):
                detail = response.text
            if code == 404:
                detail = f"Not found: {path}. Check the system id and that your key belongs to its organisation. {detail}"
            raise FairMindError(f"{method} {path} failed: {detail}", code)
        try:
            return response.json()
        except ValueError as exc:
            raise FairMindError(f"{method} {path} returned something that is not JSON", code) from exc

    def _upload(self, path: str, csv_path: PathLike, data: Dict[str, str]) -> Any:
        p = Path(csv_path)
        if not p.is_file():
            raise FairMindError(f"No such file: {p}")
        with p.open("rb") as handle:
            return self._call("POST", path, data=data, files={"file": (p.name, handle, "text/csv")})

    # -- reads ---------------------------------------------------------------

    def systems(self) -> List[System]:
        return self._call("GET", f"{GOV}/systems")

    def gate(self, system_id: str) -> Gate:
        return self._call("GET", f"{GOV}/systems/{system_id}/gate")

    def clause_map(self, system_id: str, frameworks: Optional[Sequence[str]] = None) -> ClauseMap:
        """The gate read per framework clause. `frameworks` filters client-side by catalogue key (EUAIA, ISO42001, ...)."""
        result = self._call("GET", f"{GOV}/systems/{system_id}/clause-map")
        if frameworks:
            wanted = {_FRAMEWORK_ALIASES.get(f.lower(), f).upper() for f in frameworks}
            result["frameworks"] = [f for f in result["frameworks"] if f["key"].upper() in wanted]
        return result

    def seals(self, system_id: str) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/systems/{system_id}/seals")

    def fairness_runs(self, system_id: str) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/systems/{system_id}/fairness-runs")

    def monitoring_runs(self, system_id: str) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/systems/{system_id}/monitoring-runs")

    # -- writes --------------------------------------------------------------

    def inspect_csv(self, system_id: str, path: PathLike) -> Dict[str, Any]:
        """Columns of a CSV with sample values and a suggested outcome/prediction/score/attributes mapping."""
        return self._upload(f"{GOV}/systems/{system_id}/fairness-runs/inspect", path, {})

    def run_fairness(
        self,
        system_id: str,
        path: PathLike,
        *,
        outcome: str,
        attributes: Union[str, Sequence[str]],
        prediction: Optional[str] = None,
        score: Optional[str] = None,
        favorable_label: Optional[str] = None,
    ) -> FairnessRun:
        if not prediction and not score:
            raise FairMindError("Give prediction (a 0/1 column) or score (a 0 to 1 column)")
        data = {"outcome": outcome, "attributes": _split(attributes)}
        for key, value in (("prediction", prediction), ("score", score), ("favorable_label", favorable_label)):
            if value:
                data[key] = value
        return self._upload(f"{GOV}/systems/{system_id}/fairness-runs", path, data)

    def run_monitoring(
        self,
        system_id: str,
        path: PathLike,
        *,
        attributes: Union[str, Sequence[str]],
        prediction: Optional[str] = None,
        score: Optional[str] = None,
        favorable_label: Optional[str] = None,
    ) -> MonitoringRun:
        if not prediction and not score:
            raise FairMindError("Give prediction (a 0/1 column) or score (a 0 to 1 column)")
        data = {"attributes": _split(attributes)}
        for key, value in (("prediction", prediction), ("score", score), ("favorable_label", favorable_label)):
            if value:
                data[key] = value
        return self._upload(f"{GOV}/systems/{system_id}/monitoring-runs", path, data)

    def attest(self, system_id: str, check: AttestableCheck, statement: str, reference: Optional[str] = None) -> Attestation:
        """Record that a person states a gate check is satisfied. Manual provenance: it attests, it never proves."""
        body: Dict[str, Any] = {"check": check, "statement": statement}
        if reference:
            body["reference"] = reference
        return self._call("POST", f"{GOV}/systems/{system_id}/attestations", json=body)

    # -- catalogue evaluations ---------------------------------------------

    def organization_id(self) -> str:
        """The organisation the evaluation endpoints act in: FAIRMIND_ORG_ID, else the key's first organisation."""
        if not getattr(self, "_org_id", None):
            org = os.environ.get("FAIRMIND_ORG_ID")
            if not org:
                orgs = self._call("GET", "/api/v1/organizations").get("organizations") or []
                if not orgs:
                    raise FairMindError("This key belongs to no organisation")
                org = orgs[0]["id"]
            self._org_id = org
        return self._org_id

    def _packs(self, method: str, path: str, **kwargs: Any) -> Any:
        params = {**kwargs.pop("params", {}), "org_id": self.organization_id()}
        return self._call(method, f"{PACKS}{path}", params=params, **kwargs)

    def evaluations(self, query: Optional[str] = None, pillar: Optional[str] = None) -> List[Dict[str, Any]]:
        """Catalogue evaluations; `runnable` is true for those FairMind computes itself."""
        params = {k: v for k, v in (("q", query), ("pillar", pillar)) if v}
        return self._packs("GET", "/evaluations", params=params)

    def evaluation_engine(self, evaluation_id: str) -> Dict[str, Any]:
        """The files (slots) and params an evaluation takes, and its live alternate if it has one."""
        return self._packs("GET", f"/evaluations/{evaluation_id}/engine")

    def evaluation_runs(self, evaluation_id: str, system_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"system_id": system_id} if system_id else {}
        return self._packs("GET", f"/evaluations/{evaluation_id}/runs", params=params)

    def run_evaluation(
        self,
        system_id: str,
        evaluation_id: str,
        files: Optional[Dict[str, PathLike]] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        live: bool = False,
        source: str = "upload",
        timeout: float = 900.0,
        poll_interval: float = 3.0,
    ) -> Dict[str, Any]:
        """Run a catalogue evaluation and return the stored run (status passed, failed or insufficient, metrics, detail).

        `files` maps the engine's slot names to local paths. `live=True` runs the evaluation's behaviour test
        against the system's connected endpoint; `source="connection"` reads the organisation's agent platform.
        Behaviour tests run as background jobs on the server; this waits for them up to `timeout` seconds.
        """
        data = {"system_id": system_id, "params": json.dumps(params or {}), "source": source}
        if live:
            data["mode"] = "live"
        with ExitStack() as stack:
            uploads = {}
            for slot, path in (files or {}).items():
                p = Path(path)
                if not p.is_file():
                    raise FairMindError(f"No such file: {p}")
                uploads[slot] = (p.name, stack.enter_context(p.open("rb")))
            result = self._packs("POST", f"/evaluations/{evaluation_id}/runs", data=data, files=uploads or None)
        job = result.get("job") if isinstance(result, dict) else None
        if not job:
            return result
        deadline = time.monotonic() + timeout
        while job["status"] not in ("done", "failed"):
            if time.monotonic() > deadline:
                raise FairMindError(f"Evaluation job {job['id']} is still running after {timeout:.0f}s; check it later")
            time.sleep(poll_interval)
            job = self._packs("GET", f"/evaluation-jobs/{job['id']}")
        if job["status"] == "failed":
            raise FairMindError(f"Evaluation {evaluation_id} failed: {job.get('error') or 'no reason given'}")
        return self._packs("GET", f"/evaluation-runs/{job['evidenceId']}")

    def evaluation_run(self, evidence_id: str) -> Dict[str, Any]:
        """A stored evaluation run (status passed, failed or insufficient, metrics, detail) by its evidence id."""
        return self._packs("GET", f"/evaluation-runs/{evidence_id}")

    # -- systems -------------------------------------------------------------

    def system(self, system_id: str) -> System:
        return self._call("GET", f"{GOV}/systems/{system_id}")

    def create_workspace(self, name: str, owner: Optional[str] = None) -> Dict[str, Any]:
        return self._call("POST", f"{GOV}/workspaces", json={"name": name, **({"owner": owner} if owner else {})})

    def create_system(
        self,
        workspace_id: str,
        name: str,
        *,
        risk_tier: str = "medium",
        lifecycle_stage: str = "assess",
        owner: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> System:
        body: Dict[str, Any] = {"workspace_id": workspace_id, "name": name, "risk_tier": risk_tier, "lifecycle_stage": lifecycle_stage, "metadata": metadata or {}}
        if owner:
            body["owner"] = owner
        return self._call("POST", f"{GOV}/systems", json=body)

    # -- evidence packs ------------------------------------------------------

    def pack_frameworks(self) -> List[Dict[str, str]]:
        return self._call("GET", f"{GOV}/packs/frameworks")

    def create_pack(self, title: str, frameworks: Union[str, Sequence[str]], system_ids: Union[str, Sequence[str]]) -> Dict[str, Any]:
        """Build a hashed inspection pack for systems and frameworks (catalogue keys such as EUAIA, ISO42001)."""
        split = lambda v: [x for x in _split(v).split(",") if x]  # noqa: E731
        return self._call("POST", f"{GOV}/packs", json={"title": title, "frameworks": split(frameworks), "system_ids": split(system_ids)})

    def packs(self) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/packs")

    def pack(self, pack_id: str) -> Dict[str, Any]:
        return self._call("GET", f"{GOV}/packs/{pack_id}")

    def download_pack(self, pack_id: str) -> Dict[str, Any]:
        """`{"manifest", "manifestHash"}`: the file `verify_pack` and `fairmind verify` take."""
        return self._call("GET", f"{GOV}/packs/{pack_id}/download")

    def share_pack(self, pack_id: str) -> Dict[str, Any]:
        """Mint an auditor token. It is returned once; only its hash is stored."""
        return self._call("POST", f"{GOV}/packs/{pack_id}/share")

    def revoke_pack_share(self, pack_id: str) -> Dict[str, Any]:
        return self._call("DELETE", f"{GOV}/packs/{pack_id}/share")

    def public_pack(self, pack_id: str, token: str) -> Dict[str, Any]:
        """The read-only pack an auditor gets from a share link. No sign-in needed; the token is the credential."""
        return self._call("GET", f"/api/v1/public/packs/{pack_id}", params={"t": token})

    def verify_pack(self, source: Union[Dict[str, Any], PathLike]) -> Dict[str, Any]:
        """Verify a pack document (dict) or a downloaded pack.json (path) offline. See the module-level `verify_pack`."""
        if isinstance(source, dict):
            return verify_pack(source)
        p = Path(source)
        if not p.is_file():
            raise FairMindError(f"No such file: {p}")
        try:
            return verify_pack(json.loads(p.read_text(encoding="utf-8")))
        except ValueError as exc:
            raise FairMindError(f"{p} is not valid JSON: {exc}") from exc

    def verify_share_link(self, link: str) -> Dict[str, Any]:
        """Fetch the pack behind a share link (`.../verify/<pack id>?t=<token>`) from this client's API, then verify it locally."""
        from urllib.parse import parse_qs, urlparse

        parts = urlparse(link)
        token = (parse_qs(parts.query).get("t") or [""])[0]
        pack_id = parts.path.rstrip("/").rsplit("/", 1)[-1]
        if not token or not pack_id:
            raise FairMindError("Not a share link: expected .../verify/<pack id>?t=<token>")
        shared = self.public_pack(pack_id, token)
        return verify_pack({"manifest": shared["manifest"], "manifestHash": shared["manifestHash"]})

    # -- findings, remediation -----------------------------------------------

    def add_finding(self, system_id: str, risk_type: str, severity: str, description: str) -> Dict[str, Any]:
        """Record a risk finding against a system. `severity` is low, medium, high or critical."""
        return self._call("POST", f"{GOV}/risks/assess", json={"systemId": system_id, "riskType": risk_type, "severity": severity, "description": description})

    def findings(self, system_id: Optional[str] = None) -> Dict[str, Any]:
        """Recorded risks with a summary, for one system or the whole organisation (`risks`, `suggested`, `summary`)."""
        return self._call("GET", f"{GOV}/dashboard/risk", params={"system_id": system_id} if system_id else {})

    def create_remediation(
        self,
        system_id: str,
        title: str,
        description: str,
        *,
        finding_id: Optional[str] = None,
        source_type: str = "risk",
        source_id: Optional[str] = None,
        owner: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[str] = None,
        retest_required: bool = True,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Open a remediation task; give `finding_id` to tie it to a recorded finding."""
        body: Dict[str, Any] = {
            "system_id": system_id, "title": title, "description": description, "source_type": source_type,
            "source_id": source_id or finding_id or system_id, "linked_risk_ids": [finding_id] if finding_id else [],
            "priority": priority, "retest_required": retest_required, "notes": notes,
        }
        for key, value in (("owner", owner), ("due_date", due_date)):
            if value:
                body[key] = value
        return self._call("POST", f"{GOV}/remediation", json=body)

    def remediation_tasks(self, system_id: str) -> Dict[str, Any]:
        """`{"tasks": [...], "summary": {...}}` for a system."""
        return self._call("GET", f"{GOV}/remediation", params={"system_id": system_id})

    def update_remediation(self, task_id: str, status: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """status: open, in_progress, blocked, ready_for_retest, resolved or closed."""
        body = {k: v for k, v in (("status", status), ("notes", notes)) if v is not None}
        return self._call("PATCH", f"{GOV}/remediation/{task_id}", json=body)

    # -- release decisions ---------------------------------------------------

    def request_approval(self, system_id: str) -> Dict[str, Any]:
        """Ask for a release decision on a system (returns the pending request; reuses one already pending)."""
        return self._call("POST", f"{GOV}/approval/system/{system_id}/request", json={})

    def approval_status(self, system_id: str) -> Dict[str, Any]:
        """`{"systemId", "request", "decisions"}`: the latest release decision request and its decisions."""
        return self._call("GET", f"{GOV}/approval/system/{system_id}")

    def decide_approval(self, request_id: str, decision: Literal["approved", "rejected"], notes: str = "") -> Dict[str, Any]:
        return self._call("POST", f"{GOV}/approval-requests/{request_id}/decision", json={"decision": decision, "notes": notes})

    # -- report snapshots ----------------------------------------------------

    def generate_report(
        self,
        system_id: str,
        report_type: Literal["compliance", "bias", "governance"],
        *,
        title: Optional[str] = None,
        frameworks: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Generate and store an audit report snapshot of the system's risks, evidence and approvals."""
        body: Dict[str, Any] = {"system_id": system_id, "report_type": report_type}
        if title:
            body["title"] = title
        if frameworks:
            body["frameworks"] = list(frameworks)
        return self._call("POST", f"{GOV}/reports/generate", json=body)

    def reports(self, system_id: str, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._call("GET", f"{GOV}/reports", params={"system_id": system_id, **({"report_type": report_type} if report_type else {})})

    def report(self, report_id: str) -> Dict[str, Any]:
        return self._call("GET", f"{GOV}/reports/{report_id}")
