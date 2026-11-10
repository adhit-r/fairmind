"""File engines for code scans, tool-call logs, disclosure inventories, licence records, erasure scans, accessibility reports and retrieval probes."""

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from typing import Any, Dict, List

import pandas as pd

from .common import Engine, EngineError, Param, Slot, columns, number, read_csv, read_json, result, split

YES = {"yes", "y", "true", "1", "granted"}
NO = {"no", "n", "false", "0", "denied", ""}
MAX_UNZIPPED = 50 * 1024 * 1024
MAX_FILES = 2000


def _name(params: Dict[str, Any], key: str, default: str) -> str:
    value = params.get(key)
    return default if value in (None, "") else str(value).strip()


def _flag(value: Any, what: str) -> bool:
    text = "" if pd.isna(value) else str(value).strip().casefold()
    if text in YES:
        return True
    if text in NO:
        return False
    raise EngineError(f"{what} has the value {value!r}; use yes or no")


def _pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 2) if whole else 0.0


# --- EV-DEV-03 security scan of AI-generated code -----------------------------------------------------

def _unpack(raw: bytes, into: str) -> int:
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        with open(os.path.join(into, "code.py"), "wb") as f:
            f.write(raw)
        return 1
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members = [m for m in z.infolist() if not m.is_dir() and m.filename.endswith(".py")]
        if len(members) > MAX_FILES or sum(m.file_size for m in members) > MAX_UNZIPPED:
            raise EngineError("The archive holds too much code to scan in one run")
        root = os.path.realpath(into)
        for m in members:
            target = os.path.realpath(os.path.join(into, m.filename))
            if not target.startswith(root + os.sep):
                raise EngineError(f"The archive has a path outside itself: {m.filename}")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(m) as src, open(target, "wb") as dst:
                dst.write(src.read())
        return len(members)


def code_scan(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    raw = files["code"]
    if not raw:
        raise EngineError("The code is empty")
    with tempfile.TemporaryDirectory() as tmp:
        count = _unpack(raw, tmp)
        if not count:
            raise EngineError("The archive has no Python files; this scan reads Python")
        # bandit parses the code and never runs it
        proc = subprocess.run([sys.executable, "-m", "bandit", "-r", tmp, "-f", "json", "-q"], capture_output=True, text=True, timeout=300)
        try:
            report = json.loads(proc.stdout)
        except ValueError:
            raise EngineError(f"The scanner failed: {proc.stderr.strip()[:300] or 'no report'}")
        findings = report.get("results", [])
        detail = [{"file": os.path.relpath(f["filename"], tmp), "line": f["line_number"], "test": f"{f['test_id']} {f['test_name']}",
                   "severity": f["issue_severity"].lower(), "confidence": f["issue_confidence"].lower(), "issue": f["issue_text"]} for f in findings]
        parse_errors = report.get("errors", [])
    by = {s: sum(r["severity"] == s for r in detail) for s in ("high", "medium", "low")}
    metrics = {"files": count, "high": by["high"], "medium": by["medium"], "low": by["low"], "threshold": 0, "unparsedFiles": len(parse_errors)}
    detail.sort(key=lambda r: ("high", "medium", "low").index(r["severity"]))
    if parse_errors and not by["high"]:
        return result("insufficient", f"{len(parse_errors)} files could not be parsed, so they were not scanned.", metrics, detail)
    return result("failed" if by["high"] else "passed",
                  f"{by['high']} high-severity findings in {count} files (threshold 0); {by['medium']} medium and {by['low']} low.", metrics, detail)


# --- EV-MON-02 tool-call anomalies -------------------------------------------------------------------

def _calls(raw: bytes, what: str, tool: str, target: str, session: str) -> pd.DataFrame:
    f = read_csv(raw, what)
    columns(f, [tool] + ([target] if target else []) + ([session] if session else []), what)
    f = f.copy()
    f["_tool"] = f[tool].astype(str).str.strip()
    f["_target"] = f[target].astype(str).str.strip() if target else ""
    f["_session"] = f[session].astype(str) if session else ""
    return f


def _transitions(f: pd.DataFrame) -> List[Any]:
    """(session, previous tool or None) for each call, in log order."""
    prev: Dict[str, str] = {}
    out = []
    for s, t in zip(f["_session"], f["_tool"]):
        out.append(prev.get(s))
        prev[s] = t
    return out


def tool_anomalies(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    tool, session = _name(params, "tool_column", "tool"), _name(params, "session_column", "")
    target = _name(params, "target_column", "")
    limit, factor = number(params, "max_score", -1), number(params, "volume_factor", 3.0)
    if not 0 <= limit <= 1:
        raise EngineError("Set the agreed anomaly score, the share of calls allowed to be unusual, between 0 and 1")
    base = _calls(files["baseline"], "The baseline log", tool, target, session)
    cur = _calls(files["calls"], "The call log", tool, target, session)
    tools = set(base["_tool"])
    targets = set(zip(base["_tool"], base["_target"]))
    seq = {(p, t) for p, t in zip(_transitions(base), base["_tool"]) if p is not None}
    detail = []
    for (n, row), prev in zip(cur.iterrows(), _transitions(cur)):
        why = []
        if row["_tool"] not in tools:
            why.append("tool not seen in the baseline")
        elif target and (row["_tool"], row["_target"]) not in targets:
            why.append("target not seen for this tool in the baseline")
        if prev is not None and (prev, row["_tool"]) not in seq and row["_tool"] in tools:
            why.append(f"sequence {prev} then {row['_tool']} not seen in the baseline")
        if why:
            detail.append({"call": int(n) + 1, "tool": row["_tool"], "target": row["_target"], "reasons": why})
    score = len(detail) / len(cur)
    share_b, share_c = base["_tool"].value_counts(normalize=True), cur["_tool"].value_counts(normalize=True)
    volume = sorted(t for t in share_c.index if t in share_b.index and share_c[t] > factor * share_b[t])
    metrics = {"calls": len(cur), "flaggedCalls": len(detail), "anomalyScore": round(score, 4), "threshold": limit, "volumeAnomalies": volume}
    fails = score > limit or bool(volume)
    summary = f"{len(detail)} of {len(cur)} calls are unusual against the baseline (score {score:.4f}, agreed {limit:g})"
    if volume:
        summary += f"; call share of {', '.join(volume)} is over {factor:g} times the baseline"
    return result("failed" if fails else "passed", summary + ".", metrics, detail)


# --- EV-TRN-01 AI disclosure shown --------------------------------------------------------------------

def disclosure(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    tc, ac, dc = _name(params, "touchpoint_column", "touchpoint"), _name(params, "ai_column", "ai_involved"), _name(params, "disclosure_column", "disclosure_shown")
    f = read_csv(files["touchpoints"], "The touchpoint inventory")
    columns(f, [tc, ac, dc], "The touchpoint inventory")
    ai = [(str(r[tc]), _flag(r[dc], dc)) for _, r in f.iterrows() if _flag(r[ac], ac)]
    if not ai:
        return result("insufficient", "No touchpoint involves AI, so there is nothing to check.", {"touchpoints": len(f), "aiTouchpoints": 0}, [])
    shown = sum(d for _, d in ai)
    detail = sorted(({"touchpoint": t, "disclosed": d} for t, d in ai), key=lambda r: r["disclosed"])
    rate = _pct(shown, len(ai))
    return result("passed" if shown == len(ai) else "failed",
                  f"{shown} of {len(ai)} touchpoints that involve AI show a disclosure ({rate:g}%, threshold 100%).",
                  {"touchpoints": len(f), "aiTouchpoints": len(ai), "withDisclosure": shown, "disclosureRate": rate, "threshold": 100}, detail)


# --- EV-DAT-10 training data licence compliance ---------------------------------------------------------

def licence_compliance(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    approved = {a.casefold() for a in split(params.get("approved_licences"))}
    if not approved:
        raise EngineError("approved_licences needs the licences your organisation accepts, comma-separated")
    lc, cc, ic = _name(params, "licence_column", "licence"), _name(params, "consent_column", ""), _name(params, "id_column", "record")
    f = read_csv(files["records"], "The licence and consent records")
    columns(f, [ic, lc] + ([cc] if cc else []), "The licence and consent records")
    detail = []
    for _, r in f.iterrows():
        why = []
        licence = "" if pd.isna(r[lc]) else str(r[lc]).strip()
        if licence.casefold() not in approved:
            why.append(f"licence {licence or 'missing'} is not approved")
        if cc and not _flag(r[cc], cc):
            why.append("no consent")
        if why:
            detail.append({"record": str(r[ic]), "reasons": why})
    return result("failed" if detail else "passed", f"{len(detail)} of {len(f)} records are outside their licence or consent terms (threshold 0).",
                  {"records": len(f), "outside": len(detail), "threshold": 0}, detail)


# --- EV-PRV-05 erasure propagation --------------------------------------------------------------------

def erasure_propagation(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    sc, stc, fc = _name(params, "subject_column", "subject_id"), _name(params, "store_column", "store"), _name(params, "found_column", "found")
    erased = read_csv(files["erasures"], "The erasure log")
    columns(erased, [sc], "The erasure log")
    scans = read_csv(files["scans"], "The store scans")
    columns(scans, [sc, stc, fc], "The store scans")
    subjects = set(erased[sc].astype(str).str.strip())
    scans = scans.assign(_s=scans[sc].astype(str).str.strip(), _t=scans[stc].astype(str).str.strip())
    stores = sorted(set(scans["_t"]))
    scanned = set(zip(scans["_s"], scans["_t"]))
    missing = [{"subject": s, "store": t, "state": "not scanned"} for s in sorted(subjects) for t in stores if (s, t) not in scanned]
    holding: Dict[str, List[str]] = {}
    for _, r in scans[scans["_s"].isin(subjects)].iterrows():
        if _flag(r[fc], fc):
            holding.setdefault(r["_t"], []).append(r["_s"])
    detail = [{"store": t, "subjects": sorted(set(v)), "state": "still holds erased data"} for t, v in sorted(holding.items())] + missing
    metrics = {"erasedSubjects": len(subjects), "stores": len(stores), "storesHolding": len(holding), "pairsNotScanned": len(missing), "threshold": 0}
    if holding:
        return result("failed", f"{len(holding)} of {len(stores)} stores still hold data of erased subjects: {', '.join(sorted(holding))}.", metrics, detail)
    if missing:
        return result("insufficient", f"{len(missing)} erased-subject and store pairs were not scanned, so erasure is not shown.", metrics, detail)
    return result("passed", f"None of {len(stores)} stores holds data of the {len(subjects)} erased subjects.", metrics, detail)


# --- EV-FAI-08 accessibility ---------------------------------------------------------------------------

def accessibility(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    report = read_json(files["report"], "The accessibility report")
    pages = report if isinstance(report, list) else [report]
    required = {r.casefold() for r in split(params.get("required_rules"))}
    passes: List[tuple] = []
    fails: List[tuple] = []
    incomplete = 0
    for n, page in enumerate(pages):
        if not isinstance(page, dict) or "violations" not in page or "passes" not in page:
            raise EngineError("The report must be an axe-core result with passes and violations")
        where = page.get("url") or f"page {n + 1}"
        passes += [(where, r["id"], None) for r in page["passes"] if not required or r["id"].casefold() in required]
        fails += [(where, r["id"], r.get("impact")) for r in page["violations"] if not required or r["id"].casefold() in required]
        incomplete += len(page.get("incomplete", []))
    total = len(passes) + len(fails)
    if not total:
        return result("insufficient", "The report holds no applicable check" + (" for the required rules" if required else "") + ".", {"checks": 0}, [])
    detail = [{"page": w, "rule": r, "impact": i} for w, r, i in fails]
    rate = _pct(len(passes), total)
    return result("passed" if not fails else "failed",
                  f"{len(passes)} of {total} accessibility checks passed ({rate:g}%, threshold 100%); {incomplete} need manual review.",
                  {"checks": total, "passed": len(passes), "violations": len(fails), "passRate": rate, "needsReview": incomplete, "threshold": 100}, detail)


# --- EV-SEC-09 vector and embedding weaknesses ----------------------------------------------------------

def _tokens(text: Any) -> set:
    return set(re.findall(r"\w+", str(text).casefold()))


def vector_weaknesses(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    qt, rt = _name(params, "tenant_column", "tenant"), _name(params, "result_tenant_column", "result_tenant")
    hits = read_csv(files["hits"], "The retrieval probe results")
    columns(hits, [qt, rt], "The retrieval probe results")
    cross = hits[hits[qt].astype(str) != hits[rt].astype(str)]
    detail = [{"queryingTenant": str(r[qt]), "returnedTenant": str(r[rt]), **({"query": str(r["query"])} if "query" in hits.columns else {})} for _, r in cross.iterrows()]
    metrics: Dict[str, Any] = {"hits": len(hits), "crossTenantHits": len(cross), "threshold": 0}
    summary = f"{len(cross)} of {len(hits)} retrieved items belong to a different tenant than the one querying (threshold 0)"
    fails = len(cross) > 0
    if files.get("inversion"):
        inv = read_csv(files["inversion"], "The inversion attempts")
        columns(inv, ["source_text", "recovered_text"], "The inversion attempts")
        sim = float(number(params, "recovery_similarity", 0.9))
        hit = 0
        for _, r in inv.iterrows():
            a, b = _tokens(r["source_text"]), _tokens(r["recovered_text"])
            hit += bool(a) and len(a & b) / len(a | b) >= sim
        rate = hit / len(inv)
        metrics.update({"inversionAttempts": len(inv), "inversionRecovered": hit, "inversionSuccess": round(rate, 4)})
        summary += f"; {hit} of {len(inv)} embeddings were inverted back to their source text"
        if params.get("max_inversion") not in (None, ""):
            limit = number(params, "max_inversion", 0.0)
            metrics["inversionThreshold"] = limit
            fails = fails or rate > limit
    return result("failed" if fails else "passed", summary + ".", metrics, detail)


ENGINES: List[Engine] = [
    Engine("EV-DEV-03", "Scans the Python code with Bandit, which reads the code without running it, and counts high-severity findings. Passes with none.",
           (Slot("code", "AI-generated code", "A Python file or a zip of the repository.", "binary"),), code_scan),
    Engine("EV-MON-02", "Compares the tool-call log with a baseline log: a call is unusual when its tool, its target for that tool, or the tool before it was never seen in the baseline. "
           "A tool whose share of calls is over the volume factor times its baseline share is flagged too. Passes at or below the agreed score.",
           (Slot("baseline", "Baseline call log", "CSV of normal tool calls with a tool column, and optionally target and session."),
            Slot("calls", "Call log", "CSV of the calls to judge, same columns.")),
           tool_anomalies, (Param("max_score", "Agreed anomaly score", "Share of calls allowed to be unusual, 0 to 1.", "number", required=True),
                            Param("target_column", "Target column", "Column naming what each call touched; leave empty to ignore targets."),
                            Param("session_column", "Session column", "Column that groups calls into sessions for the sequence check."),
                            Param("volume_factor", "Volume factor", "Default 3.", "number"))),
    Engine("EV-TRN-01", "Counts the touchpoints that involve AI and checks that each shows a disclosure. Passes at 100%.",
           (Slot("touchpoints", "Touchpoint inventory", "CSV with touchpoint, ai_involved and disclosure_shown columns (yes or no)."),), disclosure),
    Engine("EV-DAT-10", "Checks each record's licence against the approved licences and, when a consent column is named, that consent is given. Passes with no record outside.",
           (Slot("records", "Licence and consent records", "CSV with a record column, a licence column and optionally a consent column."),),
           licence_compliance, (Param("approved_licences", "Approved licences", "Licences your organisation accepts, comma-separated.", required=True),
                                Param("consent_column", "Consent column", "Column holding yes or no consent; leave empty to check licences only."))),
    Engine("EV-PRV-05", "Takes each erased subject and each scanned store and checks the scan found none of the subject's data there. A pair that was not scanned leaves the result open.",
           (Slot("erasures", "Erasure log", "CSV with a subject_id column of subjects whose erasure was requested."),
            Slot("scans", "Store scans", "CSV with subject_id, store and found (yes or no): one row per subject and store searched.")),
           erasure_propagation),
    Engine("EV-FAI-08", "Reads an axe-core accessibility report and counts passed rules against violated rules. Passes with no violation.",
           (Slot("report", "Accessibility report", "An axe-core result as JSON, or a list of results for several pages.", "json"),),
           accessibility, (Param("required_rules", "Required rules", "Rule IDs that must pass, comma-separated; empty means every rule in the report."),)),
    Engine("EV-SEC-09", "Counts retrieved items that belong to a different tenant than the one that queried, and optionally the embeddings inverted back to their source text. Passes with no cross-tenant hit.",
           (Slot("hits", "Retrieval probe results", "CSV with tenant and result_tenant: one row per item a probe query returned."),
            Slot("inversion", "Inversion attempts", "Optional CSV with source_text and recovered_text.", required=False)),
           vector_weaknesses, (Param("max_inversion", "Largest inversion success", "Share of inverted embeddings accepted, 0 to 1; empty reports it without a limit.", "number"),
                               Param("recovery_similarity", "Recovery similarity", "Word overlap that counts as recovered, default 0.9.", "number"))),
]
