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
    "describe_evaluation for the files and params one takes, then run_evaluation. "
    "To hand work to an auditor, create_evidence_pack (share=true mints a link) and verify_evidence_pack checks a pack offline. "
    "record_finding and create_remediation_task track issues, request_release_approval asks a person to decide "
    "(this server never approves a release itself), and generate_report stores an audit snapshot."
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
    def get_system(system_id: str) -> CallToolResult:
        """One AI system: name, owner, risk tier, lifecycle stage and metadata."""
        s = fm().system(system_id)
        return _result(f"{s.get('name', '')}  tier {s.get('riskTier', '')}  stage {s.get('lifecycleStage', '')}  id {s.get('id', '')}", dict(s))

    @server.tool()
    @guarded
    def register_system(
        name: str,
        risk_tier: Literal["low", "medium", "high", "critical"] = "medium",
        lifecycle_stage: Literal["onboard", "assess", "govern", "remediate", "operate"] = "assess",
        owner: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> CallToolResult:
        """Register an AI system. Without `workspace_id` it goes into the organisation's first workspace, or a new one named Default when there is none. Use the risk tier the user states; do not guess one."""
        client = fm()
        if not workspace_id:
            existing = client.workspaces()
            workspace_id = existing[-1]["id"] if existing else client.create_workspace("Default")["id"]
        s = client.create_system(workspace_id, name, risk_tier=risk_tier, lifecycle_stage=lifecycle_stage, owner=owner)
        return _result(f"Registered {s.get('name', '')}  tier {s.get('riskTier', '')}  id {s.get('id', '')}", dict(s))

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

    @server.tool()
    @guarded
    def create_evidence_pack(title: str, frameworks: List[str], system_ids: List[str], share: bool = False) -> CallToolResult:
        """Build a hashed inspection pack of the chosen systems' evidence and clause maps. `frameworks` are catalogue keys such as EUAIA or ISO42001. `share=true` also mints a read-only auditor token (shown once; the link is /verify/<pack id>?t=<token> on the FairMind site)."""
        pack = fm().create_pack(title, frameworks, system_ids)
        out = dict(pack)
        lines = [f"Pack {pack['id']}  {pack['title']}  hash {pack['manifestHash']}"]
        if share:
            shared = fm().share_pack(pack["id"])
            out["share"] = shared
            lines.append(f"Auditor token (shown once): {shared['token']}  expires {shared['expiresAt']}")
        return _result("\n".join(lines), out)

    @server.tool()
    @guarded
    def verify_evidence_pack(path: Optional[str] = None, link: Optional[str] = None, pack_id: Optional[str] = None) -> CallToolResult:
        """Check an inspection pack: recompute its manifest hash and each system's evidence chain head and say whether it is intact. Give one of `path` (a downloaded pack.json on this machine, checked offline), `link` (an auditor share link, fetched then checked locally) or `pack_id` (a pack of the signed-in organisation)."""
        if sum(bool(x) for x in (path, link, pack_id)) != 1:
            raise ToolError("Give exactly one of path, link or pack_id")
        client = fm()
        result = client.verify_pack(path) if path else client.verify_share_link(link) if link else client.verify_pack(client.download_pack(pack_id))
        lines = [f"{result['title']}: {'INTACT' if result['intact'] else 'DOES NOT VERIFY'}", f"  manifest hash {'ok' if result['hashOk'] else 'MISMATCH'} {result['actual']}"]
        lines += [f"  {'ok' if s['intact'] else 'BROKEN'} {s['name']}: {s['evidence']} evidence records" for s in result["systems"]]
        return _result("\n".join(lines), result)

    @server.tool()
    @guarded
    def record_finding(system_id: str, risk_type: str, severity: Literal["low", "medium", "high", "critical"], description: str) -> CallToolResult:
        """Record a risk finding against a system (for example risk_type "bias" or "privacy"). Use what was actually observed; never invent one."""
        finding = fm().add_finding(system_id, risk_type, severity, description)
        return _result(f"Finding {finding['id']}: {finding['title']}, {finding['severity']}, {finding['status']}", dict(finding))

    @server.tool()
    @guarded
    def list_findings(system_id: Optional[str] = None) -> CallToolResult:
        """Recorded findings (risks) with counts by severity, and, when `system_id` is given, that system's remediation tasks."""
        found = fm().findings(system_id)
        out: Dict[str, Any] = dict(found)
        lines = [f"{r['id']}  {r['severity']}  {r['status']}  {r['title']}" for r in found["risks"]] or ["No findings recorded."]
        if system_id:
            tasks = fm().remediation_tasks(system_id)
            out["remediation"] = tasks
            lines += [f"task {t['id']}  {t['priority']}  {t['status']}  {t['title']}" for t in tasks["tasks"]]
        return _result("\n".join(lines), out)

    @server.tool()
    @guarded
    def create_remediation_task(
        system_id: str,
        title: str,
        description: str,
        finding_id: Optional[str] = None,
        priority: Literal["low", "medium", "high", "critical"] = "medium",
        owner: Optional[str] = None,
    ) -> CallToolResult:
        """Open a remediation task for a system, optionally tied to a finding id from record_finding or list_findings."""
        task = fm().create_remediation(system_id, title, description, finding_id=finding_id, priority=priority, owner=owner)
        return _result(f"Task {task['id']}: {task['title']}, {task['priority']}, {task['status']}", dict(task))

    @server.tool()
    @guarded
    def update_remediation_task(
        task_id: str,
        status: Optional[Literal["open", "in_progress", "blocked", "ready_for_retest", "resolved", "closed"]] = None,
        notes: Optional[str] = None,
    ) -> CallToolResult:
        """Move a remediation task to a new status and/or add notes."""
        task = fm().update_remediation(task_id, status, notes)
        return _result(f"Task {task['id']}: {task['status']}", dict(task))

    @server.tool()
    @guarded
    def request_release_approval(system_id: str) -> CallToolResult:
        """Ask for a release decision on a system, or read where the latest request stands. A person approves or rejects it in FairMind; this server cannot."""
        client = fm()
        client.request_approval(system_id)
        status = client.approval_status(system_id)
        req = status["request"]
        return _result(f"Release decision: {req['status']}, request {req['id']}", dict(status))

    @server.tool()
    @guarded
    def generate_report(system_id: str, report_type: Literal["compliance", "bias", "governance"], title: Optional[str] = None) -> CallToolResult:
        """Generate and store an audit report snapshot (risks, evidence, approvals) for a system, and list the earlier ones."""
        client = fm()
        report = client.generate_report(system_id, report_type, title=title)
        earlier = client.reports(system_id, report_type)
        return _result(f"Report {report['id']}: {report['title']} ({len(earlier)} stored {report_type} reports)", {"report": report, "reports": earlier})

    return server


def main() -> None:
    create_server().run()  # stdio
