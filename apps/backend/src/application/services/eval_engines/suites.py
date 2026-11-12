"""Compositions of engines that already exist, and evaluations that read results and records FairMind or the organisation holds.

Sector suites run their component evaluations on the files given and report each component's verdict; the suite passes
only when every component passes. Release regression reads the latest stored result of each required evaluation.
Reproducibility, incident regression, evidence trace and data lineage completeness, explanation quality and
explanation stability read records or per-case measurements uploaded as files.
"""

import json
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from . import agentic, assess, model, ops
from .common import Engine, EngineError, Param, Slot, columns, number, read_csv, read_json, result, split


def _pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 2) if whole else 0.0


def _name(params: Dict[str, Any], key: str, default: str) -> str:
    value = params.get(key)
    return default if value in (None, "") else str(value).strip()


# --- EV-OVS-04 explanation quality -------------------------------------------------------------------

def explanation_quality(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    names = [_name(params, "original", "score_original"), _name(params, "top_removed", "score_top_removed"),
             _name(params, "bottom_removed", "score_bottom_removed")]
    frame = read_csv(files["explanations"], "The explanation tests")
    columns(frame, names, "The explanation tests")
    d = frame[names].apply(pd.to_numeric, errors="coerce")
    if d.isna().any().any():
        raise EngineError(f"{', '.join(names)} must be a number in every row")
    drop_top = (d[names[0]] - d[names[1]]).abs()
    drop_bottom = (d[names[0]] - d[names[2]]).abs()
    faithful = drop_top > drop_bottom
    score = float(faithful.mean())
    detail = [{"case": i + 1, "dropWhenTopRemoved": round(float(a), 4), "dropWhenBottomRemoved": round(float(b), 4), "faithful": bool(f)}
              for i, (a, b, f) in enumerate(zip(drop_top, drop_bottom, faithful))]
    metrics = {"cases": len(d), "faithfulness": round(score, 4), "meanComprehensiveness": round(float(drop_top.mean()), 4)}
    floor = params.get("min_faithfulness")
    if floor in (None, ""):
        return result("insufficient", f"Faithfulness is {score:.4f}, but no agreed score was given to judge it against.", metrics, detail)
    floor = number(params, "min_faithfulness", 0.0)
    metrics["threshold"] = floor
    ok = score >= floor
    return result("passed" if ok else "failed",
                  f"Removing the features an explanation ranks highest changed the output more than removing the lowest in {int(faithful.sum())} of {len(d)} cases "
                  f"(faithfulness {score:.4f}, agreed score {floor:g}).", metrics, detail)


# --- EV-OVS-05 explanation stability ----------------------------------------------------------------

def explanation_stability(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    pair, feat = _name(params, "pair_column", "pair"), _name(params, "feature_column", "feature")
    a, b = _name(params, "original", "attribution_original"), _name(params, "perturbed", "attribution_perturbed")
    frame = read_csv(files["pairs"], "The explanation pairs")
    columns(frame, [pair, feat, a, b], "The explanation pairs")
    for c in (a, b):
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    if frame[[a, b]].isna().any().any():
        raise EngineError(f"{a} and {b} must be a number in every row")
    detail = []
    for key, g in frame.groupby(pair, sort=True):
        x, y = g[a].to_numpy(float), g[b].to_numpy(float)
        nx, ny = np.linalg.norm(x), np.linalg.norm(y)
        if nx == 0 or ny == 0:
            raise EngineError(f"Pair {key} has an all-zero explanation, so its similarity is undefined")
        detail.append({"pair": str(key), "features": len(g), "cosineSimilarity": round(float(x @ y / (nx * ny)), 4)})
    sims = [r["cosineSimilarity"] for r in detail]
    mean = float(np.mean(sims))
    metrics = {"pairs": len(detail), "meanSimilarity": round(mean, 4), "minSimilarity": min(sims)}
    floor = params.get("min_similarity")
    if floor in (None, ""):
        return result("insufficient", f"Mean explanation similarity is {mean:.4f}, but no agreed similarity was given to judge it against.", metrics, detail)
    floor = number(params, "min_similarity", 0.0)
    metrics["threshold"] = floor
    detail.sort(key=lambda r: r["cosineSimilarity"])
    return result("passed" if mean >= floor else "failed",
                  f"Mean cosine similarity between the explanations of {len(detail)} paired inputs is {mean:.4f} (agreed {floor:g}); lowest {min(sims):.4f}.",
                  metrics, detail)


# --- sector suites ------------------------------------------------------------------------------------

FAIRNESS_PARAMS = (
    Param("attributes", "Protected attributes", "Column names, comma-separated (at least two when the suite also checks intersections).", required=True),
    Param("y_pred", "Decision column", "The system's decision, default y_pred."),
    Param("y_true", "Outcome column", "The true outcome, default y_true."),
    Param("favorable", "Favourable value", "The decision value that counts as favourable; empty reads 0/1 columns."),
    Param("max_gap", "Largest gap", "For intersections: the largest selection-rate gap accepted, default 0.1.", "number"),
    Param("min_slice", "Smallest slice", "For intersections: fewest records for a slice to count, default 30.", "number"),
)


def _fairness_payload(files: Dict[str, bytes], params: Dict[str, Any], cache: Dict[str, Any]) -> Dict[str, Any]:
    if "payload" not in cache:
        from src.application.services.fairness_run_service import FairnessRunError, run_fairness

        fav = params.get("favorable")
        try:
            cache["payload"] = run_fairness(
                files["decisions"], outcome=_name(params, "y_true", "y_true"), prediction=_name(params, "y_pred", "y_pred"),
                attributes=split(params.get("attributes")), favorable_label=None if fav in (None, "") else fav,
            )
        except FairnessRunError as exc:
            raise EngineError(str(exc))
    return cache["payload"]


def _fairness_part(evaluation: str) -> Callable[..., Dict[str, Any]]:
    """The same rule that reads a stored fairness run onto the evaluations page, applied to a run made from the decisions file."""
    def run(files, params, cache):
        from src.application.services.evaluation_results import RULES

        verdict = RULES[evaluation][1](_fairness_payload(files, params, cache))
        if verdict is None:
            return result("insufficient", "The decisions do not speak to this evaluation (for the India-specific check, name an attribute such as caste, religion, region or language).", {})
        return result(verdict[0], verdict[1] + ".", {})
    return run


def _engine(engine_id: str) -> Engine:
    return next(e for m in (model, agentic, assess, ops) for e in m.ENGINES if e.id == engine_id)


def _file_part(engine_id: str) -> Callable[..., Dict[str, Any]]:
    engine = _engine(engine_id)
    return lambda files, params, cache: engine.run(files, params)


def _part(engine_id: str):
    engine = _engine(engine_id)
    return (_file_part(engine_id), engine.slots, engine.params)


def _explanation_part(fn):
    return lambda files, params, cache: fn(files, params)


EXPLAIN_SLOT = Slot("explanations", "Explanation tests", "CSV with score_original, score_top_removed and score_bottom_removed: the model's output on each case, then with the "
                    "features its explanation ranks highest removed, then with those it ranks lowest removed.")
EXPLAIN_PARAMS = (Param("min_faithfulness", "Agreed faithfulness", "Lowest share of cases where removing the top-ranked features changes the output more than the bottom-ranked, 0 to 1.", "number"),)
ACCURACY = next(e for e in model.ENGINES if e.id == "EV-TST-01")
DECISIONS = Slot("decisions", "Decisions", "CSV of the system's decisions with the outcome and the protected attribute columns.")
PARTS: Dict[str, Tuple[Callable[..., Dict[str, Any]], Tuple[Slot, ...], Tuple[Param, ...]]] = {
    "EV-TST-01": (_file_part("EV-TST-01"), ACCURACY.slots, ACCURACY.params),
    "EV-FAI-01": (_fairness_part("EV-FAI-01"), (DECISIONS,), FAIRNESS_PARAMS[:4]),
    "EV-FAI-02": (_fairness_part("EV-FAI-02"), (DECISIONS,), FAIRNESS_PARAMS[:4]),
    "EV-FAI-06": (_fairness_part("EV-FAI-06"), (DECISIONS,), FAIRNESS_PARAMS[:4]),
    "EV-FAI-03": (_file_part("EV-FAI-03"), (DECISIONS,), FAIRNESS_PARAMS),
    "EV-OVS-04": (_explanation_part(explanation_quality), (EXPLAIN_SLOT,), EXPLAIN_PARAMS),
    **{i: _part(i) for i in ("EV-OVS-03", "EV-DEV-03", "EV-SEC-16")},
}
# The behaviour test EV-TST-04 (robustness) and EV-RSK-01, EV-PRV-04 call the system and run on their own, so a suite made of
# uploaded files leaves them out; each suite says so in its method.
SECTORS: Dict[str, Tuple[str, ...]] = {
    "EV-USE-01": ("EV-TST-01", "EV-FAI-01", "EV-FAI-03"),
    "EV-USE-02": ("EV-TST-01", "EV-FAI-01", "EV-FAI-06", "EV-OVS-04"),
    "EV-USE-07": ("EV-TST-01", "EV-FAI-01", "EV-OVS-04"),
    "EV-USE-08": ("EV-TST-01", "EV-FAI-01", "EV-FAI-03"),
    "EV-USE-09": ("EV-TST-01", "EV-FAI-01", "EV-FAI-02"),
    "EV-USE-05": ("EV-TST-01", "EV-RSK-01", "EV-OVS-03", "EV-PRV-04"),
    "EV-USE-06": ("EV-DEV-03", "EV-SEC-16", "EV-SEC-20"),
}


def _suite_engine(suite_id: str, listed: Tuple[str, ...]) -> Engine:
    parts = tuple(p for p in listed if p in PARTS)
    apart = [p for p in listed if p not in PARTS]
    slots: Dict[str, Slot] = {}
    params: Dict[str, Param] = {}
    for p in parts:
        for s in PARTS[p][1]:
            slots.setdefault(s.name, s)
        for q in PARTS[p][2]:
            params.setdefault(q.name, q)

    def run(files: Dict[str, bytes], values: Dict[str, Any]) -> Dict[str, Any]:
        cache: Dict[str, Any] = {}
        rows = []
        for p in parts:
            try:
                out = PARTS[p][0](files, values, cache)
            except EngineError as exc:
                raise EngineError(f"{p}: {exc}")
            rows.append({"evaluation": p, "status": out["status"], "summary": out["summary"], "metrics": out["metrics"]})
        count = {s: sum(r["status"] == s for r in rows) for s in ("passed", "failed", "insufficient")}
        status = "failed" if count["failed"] else "insufficient" if count["insufficient"] else "passed"
        bad = [f"{r['evaluation']} {r['status']}" for r in rows if r["status"] != "passed"]
        summary = f"{count['passed']} of {len(rows)} components passed" + (f"; {', '.join(bad)}" if bad else "") + "."
        return result(status, summary, {"components": len(rows), **count, **{r["evaluation"]: r["status"] for r in rows}}, rows)

    method = ("Runs " + ", ".join(parts) + " on the files given and passes only when every component passes. "
              + (f"These call the system or read its platform and run on their own: {', '.join(apart)}." if apart else
                 "The behaviour tests that call the system (for example EV-TST-04) run on their own."))
    return Engine(suite_id, method, tuple(slots.values()), run, tuple(params.values()))


# --- EV-REL-01 release regression ----------------------------------------------------------------------

def collect_results(db, org_id: str, system_id: str) -> Dict[str, bytes]:
    """The latest stored result of every evaluation for one AI system."""
    from src.application.services.evaluation_results import results

    rows = [{"evaluationId": ev, "status": s["status"], "detail": s["detail"], "at": s["at"]}
            for ev, r in results(db, org_id).items() for s in r["systems"] if s["systemId"] == system_id]
    return {"results": json.dumps(rows).encode()}


def release_regression(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    required = split(params.get("required"))
    if not required:
        raise EngineError("required needs the evaluation IDs a release must pass, comma-separated")
    stored = json.loads(files["results"].decode() or "[]")
    latest: Dict[str, Dict[str, Any]] = {}
    for r in sorted(stored, key=lambda r: str(r.get("at") or "")):
        latest[r["evaluationId"]] = r
    rows = [{"evaluation": ev, "status": latest[ev]["status"] if ev in latest else "not_run", "summary": (latest.get(ev) or {}).get("detail"),
             "at": (latest.get(ev) or {}).get("at")} for ev in required]
    failed = [r["evaluation"] for r in rows if r["status"] == "failed"]
    open_ = [r["evaluation"] for r in rows if r["status"] not in ("passed", "failed")]
    metrics = {"required": len(rows), "failed": len(failed), "notPassed": len(open_), "threshold": 0}
    if failed:
        return result("failed", f"{len(failed)} of {len(rows)} required evaluations failed in their latest run: {', '.join(failed)}.", metrics, rows)
    if open_:
        return result("insufficient", f"No passing latest result for {', '.join(open_)}, so the release cannot be cleared.", metrics, rows)
    return result("passed", f"All {len(rows)} required evaluations passed in their latest run.", metrics, rows)


# --- EV-TST-09 reproducibility ------------------------------------------------------------------------

def reproducibility(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    idc, rc = _name(params, "id_column", "id"), _name(params, "result_column", "result")
    tol, floor = number(params, "tolerance", 0.0), number(params, "min_agreement", 1.0)
    cfg_a, cfg_b = read_json(files["config_a"], "The first run's configuration"), read_json(files["config_b"], "The second run's configuration")
    runs = []
    for slot, label in (("run_a", "The first run"), ("run_b", "The second run")):
        f = read_csv(files[slot], label)
        columns(f, [idc, rc], label)
        if f[idc].duplicated().any():
            raise EngineError(f"{label} has a repeated {idc}")
        runs.append(f.set_index(idc)[rc].astype(str).str.strip().to_dict())
    a, b = runs
    if cfg_a != cfg_b:
        return result("insufficient", "The two runs used different configurations, so their agreement says nothing about reproducibility.",
                      {"configurationsEqual": False}, [])

    def same(x, y) -> bool:
        try:
            return abs(float(x) - float(y)) <= tol
        except ValueError:
            return x == y

    ids = sorted(set(a) | set(b), key=str)
    detail = [{"id": i, "first": a.get(i), "second": b.get(i), "agree": i in a and i in b and same(a[i], b[i])} for i in ids]
    agree = sum(r["agree"] for r in detail)
    rate = agree / len(detail)
    metrics = {"items": len(detail), "agreed": agree, "agreement": round(rate, 4), "threshold": floor, "tolerance": tol,
               "onlyInOneRun": sum(i not in a or i not in b for i in ids), "configurationsEqual": True}
    detail.sort(key=lambda r: r["agree"])
    return result("passed" if rate >= floor else "failed",
                  f"{agree} of {len(detail)} items agree across the two runs ({rate:.2%}; required {floor:.2%}, tolerance {tol:g}).", metrics, detail)


# --- EV-INC-01 incident regression --------------------------------------------------------------------

def incident_regression(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    idc, sc, tc = _name(params, "id_column", "id"), _name(params, "status_column", "status"), _name(params, "test_column", "regression_test")
    closed_values = {v.casefold() for v in split(params.get("closed_values") or "closed,resolved")}
    f = read_csv(files["incidents"], "The incident records")
    columns(f, [idc, sc, tc], "The incident records")
    known = None
    if files.get("tests"):
        t = read_csv(files["tests"], "The test list")
        columns(t, ["id"], "The test list")
        known = set(t["id"].astype(str).str.strip())
    closed = f[f[sc].astype(str).str.strip().str.casefold().isin(closed_values)]
    if closed.empty:
        return result("insufficient", "No incident is closed, so there is nothing to test.", {"incidents": len(f), "closed": 0}, [])
    detail = []
    for _, r in closed.iterrows():
        link = "" if pd.isna(r[tc]) else str(r[tc]).strip()
        detail.append({"incident": str(r[idc]), "regressionTest": link, "covered": bool(link) and (known is None or link in known)})
    covered = sum(r["covered"] for r in detail)
    rate = _pct(covered, len(detail))
    detail.sort(key=lambda r: r["covered"])
    return result("passed" if covered == len(detail) else "failed",
                  f"{covered} of {len(detail)} closed incidents have a regression test ({rate:g}%, threshold 100%).",
                  {"closed": len(detail), "withTest": covered, "coverage": rate, "threshold": 100}, detail)


# --- EV-SLF-03 evidence trace completeness ------------------------------------------------------------

def _dig(item: Any, path: str) -> Any:
    for part in path.split("."):
        if not isinstance(item, dict) or part not in item:
            return None
        item = item[part]
    return item


def trace_completeness(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    fields = split(params.get("required_fields") or "model,prompt,tool_calls,content_hash")
    items = read_json(files["evidence"], "The evidence export")
    if isinstance(items, dict):
        items = items.get("items") or items.get("evidence")
    if not isinstance(items, list) or not items or not all(isinstance(i, dict) for i in items):
        raise EngineError("The evidence export must be a JSON list of evidence items (or an object with an items list)")
    detail = []
    for n, item in enumerate(items):
        # an empty list is a recorded trace of no tool calls; null and empty text are not
        missing = [f for f in fields if (v := _dig(item, f)) is None or (isinstance(v, str) and not v.strip())]
        detail.append({"item": str(item.get("id", n + 1)), "missing": missing, "complete": not missing})
    done = sum(r["complete"] for r in detail)
    detail.sort(key=lambda r: r["complete"])
    return result("passed" if done == len(detail) else "failed",
                  f"{done} of {len(detail)} evidence items carry every required field ({_pct(done, len(detail)):g}%, threshold 100%).",
                  {"items": len(detail), "complete": done, "completeness": _pct(done, len(detail)), "threshold": 100, "requiredFields": fields}, detail)


# --- EV-DAT-09 data lineage completeness --------------------------------------------------------------

def lineage_completeness(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    dc = _name(params, "dataset_column", "dataset")
    fields = split(params.get("required_fields") or "source,licence,transformations")
    f = read_csv(files["lineage"], "The lineage records")
    columns(f, [dc, *fields], "The lineage records")
    detail = []
    for _, r in f.iterrows():
        missing = [c for c in fields if pd.isna(r[c]) or not str(r[c]).strip()]
        detail.append({"dataset": str(r[dc]), "missing": missing, "complete": not missing})
    done = sum(r["complete"] for r in detail)
    detail.sort(key=lambda r: r["complete"])
    return result("passed" if done == len(detail) else "failed",
                  f"{done} of {len(detail)} datasets have source, licence and transformations recorded ({_pct(done, len(detail)):g}%, threshold 100%).",
                  {"datasets": len(detail), "complete": done, "completeness": _pct(done, len(detail)), "threshold": 100, "requiredFields": fields}, detail)


ENGINES: List[Engine] = [_suite_engine(i, parts) for i, parts in SECTORS.items()] + [
    Engine("EV-OVS-04", "Reads, per case, the model's output on the input and with the features its explanation ranks highest and lowest removed; an "
           "explanation is faithful in a case when removing the highest-ranked changes the output more. Passes at or above the agreed share.",
           (EXPLAIN_SLOT,), explanation_quality, EXPLAIN_PARAMS),
    Engine("EV-OVS-05", "Reads the feature attributions of each original input and its slightly changed twin and takes the cosine similarity of each pair. "
           "Passes when the mean is at or above the agreed similarity.",
           (Slot("pairs", "Explanation pairs", "CSV with pair, feature, attribution_original and attribution_perturbed: one row per feature of each pair."),),
           explanation_stability, (Param("min_similarity", "Agreed similarity", "Lowest mean cosine similarity, 0 to 1.", "number"),)),
    Engine("EV-REL-01", "Reads the latest stored result of each required evaluation for this AI system. Fails on any failed result; a required evaluation with no passing result cannot clear the release.",
           (), release_regression, (Param("required", "Required evaluations", "Evaluation IDs the release must pass, comma-separated.", required=True),),
           collect=collect_results),
    Engine("EV-TST-09", "Compares per-item results of two runs made under the same pinned configuration; the share of items that agree (within the tolerance for numbers) must reach the required agreement.",
           (Slot("run_a", "First run results", "CSV with id and result columns."), Slot("run_b", "Second run results", "CSV with id and result columns."),
            Slot("config_a", "First run configuration", "JSON of the pinned configuration: seed, model version, parameters.", "json"),
            Slot("config_b", "Second run configuration", "JSON of the pinned configuration of the second run.", "json")),
           reproducibility, (Param("min_agreement", "Required agreement", "Share of items that must agree, 0 to 1; default 1 (100%).", "number"),
                             Param("tolerance", "Numeric tolerance", "Largest difference between two numeric results still counted as agreeing; default 0.", "number"))),
    Engine("EV-INC-01", "Counts closed incidents that name a regression test; with a test list, the named test must be in it. Passes at 100%.",
           (Slot("incidents", "Incident records", "CSV with id, status and regression_test columns."),
            Slot("tests", "Test list", "Optional CSV with an id column listing the tests or evaluation runs that exist.", required=False)),
           incident_regression, (Param("closed_values", "Closed statuses", "Status values that mean closed, comma-separated; default closed,resolved."),)),
    Engine("EV-SLF-03", "Checks each evidence item for the required fields (default model, prompt, tool_calls, content_hash; dotted paths allowed). Passes at 100% complete.",
           (Slot("evidence", "Evidence export", "JSON list of evidence items.", "json"),),
           trace_completeness, (Param("required_fields", "Required fields", "Comma-separated fields every item must carry."),)),
    Engine("EV-DAT-09", "Checks each dataset's lineage record for a source, licence and transformations. Passes at 100% complete.",
           (Slot("lineage", "Lineage records", "CSV with a dataset column and source, licence and transformations columns."),),
           lineage_completeness, (Param("required_fields", "Required fields", "Comma-separated columns every dataset must have filled; default source,licence,transformations."),)),
]
