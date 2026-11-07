"""FairMind MCP server: tools a coding agent uses to ask "may this ship?" and to run tests.

Configuration is the SDK's: FAIRMIND_API_URL and FAIRMIND_API_KEY. Every tool returns a compact
text summary and the full API response as structured content.
"""

from __future__ import annotations

import functools
from typing import Any, Dict, List, Literal, Optional

from fairmind import FairMind, FairMindError
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import CallToolResult, TextContent

VERDICT_WORD = {"go": "GO", "conditional_go": "CONDITIONAL GO", "no_go": "NO GO"}
STATE_MARK = {"proven": "+", "attested": "~", "open": "-"}

INSTRUCTIONS = (
    "FairMind grades the evidence behind an AI system and answers whether it may ship. "
    "Call list_systems to find a system id, release_gate to read the verdict, run_fairness_test or "
    "record_monitoring_snapshot with a CSV on this machine to add measured evidence, and attest_check "
    "only for a statement the user has confirmed. For the wider catalogue (drift, leakage, prompt injection, "
    "jailbreaks, counterfactual flip rate, agent configuration and more), call list_evaluations, then "
    "describe_evaluation for the files and params one takes, then run_evaluation."
)


def _result(text: str, structured: Dict[str, Any]) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], structuredContent=structured)


def render_gate(gate: Dict[str, Any]) -> str:
    lines = [
        f"{VERDICT_WORD.get(gate['verdict'], gate['verdict'])}  confidence {gate['confidence']:.2f} ({gate.get('band', 'n/a')})  "
        f"{gate.get('proven', 0)} proven, {gate.get('attested', 0)} attested, {gate.get('open', 0)} open"
    ]
    for check in gate.get("checks", []):
        conf = f" {check['confidence']:.2f}" if check.get("confidence") else ""
        lines.append(f"  {STATE_MARK.get(check['state'], '?')} {check['label']}: {check['state']}{conf}")
    if "approvalStatus" in gate:
        lines.append(f"  Release decision: {gate['approvalStatus'].replace('_', ' ')}")
    lines.extend(f"  Reason: {reason}" for reason in gate.get("reasons", []))
    return "\n".join(lines)


def _fmt(value: Optional[float], ok: Optional[bool]) -> str:
    return "n/a" if value is None else f"{value:.3f}{'' if ok in (None, True) else '!'}"


def render_fairness(run: Dict[str, Any]) -> str:
    result = run["result"]
    head = "All checks within thresholds" if result["all_checks_pass"] else "At least one check outside thresholds"
    lines = [f"{head}, {result['rows']} rows, evidence {run['evidenceId']}"]
    for attr in result["attributes"]:
        checks = attr["checks"]
        cal = attr.get("calibration")
        lines.append(
            f"  {attr['attribute']}: impact ratio {_fmt(attr['disparate_impact_ratio'], checks.get('disparate_impact'))}, "
            f"equal opportunity gap {_fmt(attr['equal_opportunity']['value'], checks.get('equal_opportunity'))}, "
            f"equalized odds gap {_fmt(attr['equalized_odds']['value'], checks.get('equalized_odds'))}, "
            f"calibration {_fmt(cal['value'] if cal else None, checks.get('calibration'))}"
        )
        if attr.get("small_groups"):
            lines.append(f"    small groups: {', '.join(attr['small_groups'])}")
    lines.append("  ! marks a value outside its threshold (impact ratio below 0.80, gap above 0.05)")
    return "\n".join(lines + ["", render_gate(run["gate"])])


def render_monitoring(run: Dict[str, Any]) -> str:
    result = run["result"]
    psi = result.get("overall_psi")
    head = "Stable against the baseline" if result["all_checks_pass"] else "Drift or disparity outside thresholds"
    lines = [
        f"{head}, {result['rows']} rows, overall score PSI {'n/a' if psi is None else f'{psi:.3f}'}, "
        f"baseline {'present' if result.get('baseline', {}).get('present') else 'none (run a fairness test first)'}, evidence {run['evidenceId']}"
    ]
    for attr in result["attributes"]:
        checks = attr["checks"]
        lines.append(
            f"  {attr['attribute']}: max rate drift {_fmt(attr.get('max_rate_drift'), checks.get('selection_rate_stable'))}, "
            f"impact ratio {_fmt(attr['disparate_impact_ratio'], checks.get('disparate_impact'))}, "
            f"worst PSI {_fmt(attr.get('worst_psi'), checks.get('score_stable'))}"
        )
    lines.append("  ! marks a value outside its threshold (rate drift above 0.05, impact ratio below 0.80, PSI at or above 0.10)")
    return "\n".join(lines + ["", render_gate(run["gate"])])


def render_evaluation_run(run: Dict[str, Any]) -> str:
    lines = [f"{run.get('evaluationId')}: {str(run.get('status', '')).upper()}, evidence {run.get('id')}"]
    if run.get("summary"):
        lines.append(f"  {run['summary']}")
    for key, value in (run.get("metrics") or {}).items():
        lines.append(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")
    return "\n".join(lines)


def render_engine(spec: Dict[str, Any]) -> str:
    def part(engine: Dict[str, Any], title: str) -> List[str]:
        out = [f"{title}: {engine['method']}"]
        out += [f"  file {s['name']} ({s['kind']}{'' if s['required'] else ', optional'}): {s['help']}" for s in engine["slots"]]
        out += [f"  param {p['name']} ({p['kind']}{', required' if p['required'] else ''}): {p['help']}" for p in engine["params"]]
        return out

    lines = part(spec, "Behaviour test against the live system" if spec.get("live") else "On files")
    if spec.get("platform"):
        lines.append("  can also read the connected agent platform instead of files (source=connection)")
    if spec.get("alternate"):
        lines += part(spec["alternate"], "Also as a behaviour test (live=true)")
    return "\n".join(lines)


def render_clause_map(cmap: Dict[str, Any]) -> str:
    lines = [f"Gate {VERDICT_WORD.get(cmap['verdict'], cmap['verdict'])}, confidence {cmap['confidence']:.2f}"]
    for fw in cmap["frameworks"]:
        c = fw["counts"]
        lines.append(f"{fw['name']} ({fw['key']}): {c['proven']} proven, {c['attested']} attested, {c['open']} open of {c['total']} clauses")
        open_clauses = [cl["control"] for cl in fw["clauses"] if cl["state"] == "open"]
        if open_clauses:
            lines.append(f"  open: {', '.join(open_clauses)}")
    return "\n".join(lines)


def create_server(client: Optional[FairMind] = None) -> FastMCP:
    """Build the server. `client` defaults to FairMind() from the environment, created on first use."""
    holder: Dict[str, FairMind] = {"client": client} if client else {}

    def fm() -> FairMind:
        if "client" not in holder:
            holder["client"] = FairMind()
        return holder["client"]

    def guarded(fn):  # surface API failures as tool errors with the server's message
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> CallToolResult:
            try:
                return fn(*args, **kwargs)
            except FairMindError as exc:
                raise ToolError(str(exc)) from exc

        return wrapper

    server = FastMCP("fairmind", instructions=INSTRUCTIONS)

    @server.tool()
    @guarded
    def list_systems() -> CallToolResult:
        """List the AI systems the configured FairMind key can see, with id, risk tier and lifecycle stage."""
        systems = fm().systems()
        if not systems:
            return _result("No systems in this organisation yet.", {"systems": []})
        lines = [f"{s.get('name', '')}  tier {s.get('riskTier', '')}  stage {s.get('lifecycleStage', '')}  id {s.get('id', '')}" for s in systems]
        return _result("\n".join(lines), {"systems": systems})

    @server.tool()
    @guarded
    def release_gate(system_id: str) -> CallToolResult:
        """May this AI system ship? Returns the verdict (go, conditional_go, no_go), confidence, the five checks (each proven, attested or open), the reasons and the release decision status (not_requested, pending, approved, rejected). A release that needs sign-off may ship only when that status is approved."""
        gate = fm().gate(system_id)
        return _result(render_gate(gate), dict(gate))

    @server.tool()
    @guarded
    def clause_map(system_id: str, frameworks: Optional[List[str]] = None) -> CallToolResult:
        """Read the release gate per regulatory clause (EU AI Act, ISO 42001, NIST AI RMF, ...). `frameworks` optionally limits it to catalogue keys such as EUAIA or ISO42001."""
        cmap = fm().clause_map(system_id, frameworks)
        return _result(render_clause_map(cmap), dict(cmap))

    @server.tool()
    @guarded
    def run_fairness_test(
        system_id: str,
        csv_path: str,
        outcome: str,
        attributes: List[str],
        prediction: Optional[str] = None,
        score: Optional[str] = None,
        favorable_label: Optional[str] = None,
    ) -> CallToolResult:
        """Run a fairness test on a CSV on this machine (one row per decision) and store it as measured evidence. `outcome` is the column with what happened, `attributes` the protected attribute columns, and `prediction` (0/1) or `score` (0 to 1) the model's output column. `favorable_label` names the favourable value when a column is not 0/1. Returns the metrics and the updated gate."""
        run = fm().run_fairness(system_id, csv_path, outcome=outcome, attributes=attributes, prediction=prediction, score=score, favorable_label=favorable_label)
        return _result(render_fairness(run), dict(run))

    @server.tool()
    @guarded
    def record_monitoring_snapshot(
        system_id: str,
        csv_path: str,
        attributes: List[str],
        prediction: Optional[str] = None,
        score: Optional[str] = None,
        favorable_label: Optional[str] = None,
    ) -> CallToolResult:
        """Compare recent production decisions in a CSV on this machine against the system's latest fairness run (selection-rate drift, impact ratio, score PSI) and store the snapshot as measured evidence. Needs `prediction` (0/1) or `score` (0 to 1)."""
        run = fm().run_monitoring(system_id, csv_path, attributes=attributes, prediction=prediction, score=score, favorable_label=favorable_label)
        return _result(render_monitoring(run), dict(run))

    @server.tool()
    @guarded
    def attest_check(
        system_id: str,
        check: Literal["data_governance", "human_oversight", "monitoring", "environmental"],
        statement: str,
        reference: Optional[str] = None,
    ) -> CallToolResult:
        """Record that a person states a gate check is satisfied (manual evidence: it attests, it never proves). Only call this with a statement the user has given or confirmed; never invent one. `statement` is at least 12 characters; `reference` optionally points at a document or ticket."""
        done = fm().attest(system_id, check, statement, reference)
        return _result(f"Attested {check}, evidence {done['evidenceId']}\n\n{render_gate(done['gate'])}", dict(done))

    @server.tool()
    @guarded
    def list_evaluations(query: Optional[str] = None) -> CallToolResult:
        """Search FairMind's evaluation catalogue (for example "drift", "injection", "leakage", "counterfactual"). Each entry says what it measures, its pass threshold and whether FairMind can run it."""
        evals = fm().evaluations(query)
        if not evals:
            return _result("No evaluation matches.", {"evaluations": []})
        lines = [f"{e['id']}  {'runnable' if e.get('runnable') else 'evidence only'}  {e['name']}: {e.get('measures') or ''}" for e in evals]
        return _result("\n".join(lines), {"evaluations": evals})

    @server.tool()
    @guarded
    def describe_evaluation(evaluation_id: str) -> CallToolResult:
        """The files and params an evaluation takes before run_evaluation, and whether it can run as a behaviour test against the live system."""
        spec = fm().evaluation_engine(evaluation_id)
        return _result(render_engine(spec), dict(spec))

    @server.tool()
    @guarded
    def run_evaluation(
        system_id: str,
        evaluation_id: str,
        files: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        live: bool = False,
        use_connection: bool = False,
    ) -> CallToolResult:
        """Run a catalogue evaluation and store the result as measured evidence. `files` maps the file names from describe_evaluation to paths on this machine. `live=true` runs its behaviour test against the system's connected endpoint, judged by the organisation's model (this can take minutes). `use_connection=true` reads the organisation's connected agent platform instead of files. Returns passed, failed or insufficient with the metrics."""
        run = fm().run_evaluation(system_id, evaluation_id, files, params, live=live, source="connection" if use_connection else "upload")
        return _result(render_evaluation_run(run), dict(run))

    return server


def main() -> None:
    create_server().run()  # stdio
