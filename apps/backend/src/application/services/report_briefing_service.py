"""The briefing at the top of each report: short sentences in which every figure is a cited fact from the model.

A briefing is a list of parts: plain text, or a fact {"fact": id, "value": shown text, "note": where it comes from,
"tone": "" | "need" | "bad"}. The template always works. When the organisation has an AI provider, its model may
reword the sentences, but only through {{fact-id}} placeholders: a reply that cites an unknown fact or writes a
digit of its own is thrown away and the template stands, so the model can never put a number on the page.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

Part = Dict[str, Any]
PLACEHOLDER = re.compile(r"\{\{([a-z0-9.\-]+)\}\}")


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


class _Facts:
    def __init__(self) -> None:
        self.facts: Dict[str, Dict[str, Any]] = {}

    def add(self, fid: str, value: str, note: str, tone: str = "") -> str:
        self.facts[fid] = {"fact": fid, "value": value, "note": note, "tone": tone}
        return "{{" + fid + "}}"


def _sentences(model: Dict[str, Any]) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    """Template sentences with {{fact}} placeholders, and the facts they cite."""
    f, out = _Facts(), []
    fw = (model.get("framework") or {}).get("name") or "the framework"
    scope = (model.get("scope") or {}).get("systemName")
    ready, road = model.get("readiness"), model.get("road")
    if ready and ready.get("total"):
        who = scope or _plural(ready["systems"], "one system", f"{ready['systems']} systems")
        note = f"{fw} requirement cells met: {ready['met']} of {ready['total']}"
        pct = f.add("readiness.pct", f"{ready['pct']}%", note)
        out.append(f"{scope} meets {pct} of its {fw} requirements." if scope else f"Across {who}, {pct} of {fw} requirements are met.")
    elif "readiness" in model:
        out.append(f"No system answers to {fw} yet, so there is no readiness to report.")
    if road and road.get("steps"):
        n = len(road["steps"])
        out.append(f"The gate's path forward lists {f.add('road.steps', str(n), 'Steps from each system’s path forward that close open requirements')} "
                   f"{_plural(n, 'step', 'steps')}; done, they take readiness to {f.add('road.forecast', str(road['forecast']) + '%', 'Readiness if every listed step is done', 'need' if road['forecast'] < 100 else '')}.")
    decisions = model.get("decisions")
    if decisions:
        oldest = max((d.get("waitingDays") or 0) for d in decisions)
        out.append(f"{f.add('decisions.count', str(len(decisions)), 'Release decisions waiting for a person', 'need')} release "
                   f"{_plural(len(decisions), 'decision waits', 'decisions wait')} for a person, the oldest for {f.add('decisions.oldest', f'{oldest} days', 'Days since the oldest request')}.")
    proof = model.get("proof")
    if proof and (backed := proof["measured"] + proof["estimated"] + proof["attested"]):
        out.append(f"{f.add('proof.measured', str(round(100 * proof['measured'] / backed)) + '%', 'Requirements backed by evidence FairMind measured, of all backed requirements')} "
                   f"of the proof was measured by FairMind; {f.add('proof.attested', str(proof['attested']), 'Requirements backed only by a person’s statement', 'need' if proof['attested'] else '')} "
                   f"{_plural(proof['attested'], 'requirement rests', 'requirements rest')} on someone’s word.")
    tasks = model.get("tasks")
    if tasks and tasks.get("open"):
        open_n, late_n = tasks["open"], tasks["overdue"]
        out.append(f"{f.add('tasks.open', str(open_n), 'Open tasks')} {_plural(open_n, 'task is', 'tasks are')} open and "
                   f"{f.add('tasks.overdue', str(late_n), 'Tasks past their due date', 'bad' if late_n else '')} {_plural(late_n, 'is', 'are')} overdue.")
    systems = model.get("systems")
    if systems is not None:
        # the same verdicts the release gate table shows, one per listed system
        no_go = sum(1 for s in systems if s.get("verdict") == "no_go")
        scope = f"in scope for {fw}" if (model.get("framework") or {}).get("key") else "registered"
        if systems:
            out.append(f"{f.add('systems.nogo', str(no_go), 'Systems whose release gate verdict is No go', 'bad' if no_go else '')} of "
                       f"{f.add('systems.listed', str(len(systems)), 'Systems listed in the release gate table')} systems {scope} "
                       f"{_plural(no_go, 'is', 'are')} not cleared for release.")
        else:
            out.append(f"No system is {scope} yet.")
    eng = model.get("engineering")
    if eng:
        failed_runs = sum(1 for x in eng.get("fixes") or [] if x.get("kind") == "evaluation")
        if failed_runs:
            out.append(f"{f.add('fixes.evaluations', str(failed_runs), 'Failed catalogue evaluations with an open finding', 'bad')} failed "
                       f"{_plural(failed_runs, 'evaluation waits', 'evaluations wait')} to be fixed and run again.")
        ungated = [t for t in eng["toolExposure"] if not t["gated"]]
        if eng["toolExposure"]:
            out.append(f"{f.add('tools.ungated', str(len(ungated)), 'High-risk agent tools that run without a person approving', 'bad' if ungated else '')} high-risk agent "
                       f"{_plural(len(ungated), 'tool runs', 'tools run')} without a person approving each call.")
    aud = model.get("auditor")
    if aud:
        ledger = aud["ledger"]
        if ledger["entries"] or not ledger["intact"]:
            out.append(f"The ledger holds {f.add('ledger.entries', str(ledger['entries']), 'Hash-chained entries across workflow runs, internal audits and seals')} entries and is "
                       f"{f.add('ledger.state', 'intact' if ledger['intact'] else 'broken', 'Every chain recomputed just now', '' if ledger['intact'] else 'bad')}.")
        else:
            out.append("Nothing is on the ledger yet: no workflow run, internal audit or sealed decision.")
        if aud["sample"]["size"]:
            out.append(f"A reproducible sample of {f.add('sample.size', str(aud['sample']['size']), 'Drawn with the newest ledger hash as seed')} evidence items is ready for testing.")
    risk = model.get("risk")
    if risk is not None:
        open_high = [r for r in risk["risks"] if r["status"] in ("open", "acceptance_pending") and r["severity"] in ("high", "critical")]
        out.append(f"{f.add('risk.high', str(len(open_high)), 'Open risks rated high or critical', 'bad' if open_high else '')} open "
                   f"{_plural(len(open_high), 'risk is', 'risks are')} rated high or critical.")
        if risk["acceptanceWaiting"]:
            n = len(risk["acceptanceWaiting"])
            out.append(f"{f.add('risk.waiting', str(n), 'Risk acceptances waiting for a second person', 'need')} risk "
                       f"{_plural(n, 'acceptance waits', 'acceptances wait')} for a second person.")
    return out, f.facts


def _parts(sentences: List[str], facts: Dict[str, Dict[str, Any]]) -> List[Part]:
    parts: List[Part] = []
    text = " ".join(sentences)
    pos = 0
    for m in PLACEHOLDER.finditer(text):
        if m.start() > pos:
            parts.append({"text": text[pos:m.start()]})
        parts.append(dict(facts[m.group(1)]))
        pos = m.end()
    if pos < len(text):
        parts.append({"text": text[pos:]})
    return parts


def template_briefing(model: Dict[str, Any]) -> Dict[str, Any]:
    sentences, facts = _sentences(model)
    return {"source": "template", "parts": _parts(sentences, facts)}


def accept_rewrite(sentences: List[str], facts: Dict[str, Dict[str, Any]], draft_count: Optional[int] = None) -> Optional[List[Part]]:
    """The model's sentences, or None when they cite an unknown fact, drop a fact, write a digit of their own, add a
    sentence with no fact in it (a claim the figures do not carry), or run longer than the draft."""
    if not sentences or not all(isinstance(s, str) for s in sentences):
        return None
    if draft_count is not None and len(sentences) > draft_count:
        return None
    if any(not PLACEHOLDER.search(s) for s in sentences):
        return None
    text = " ".join(sentences)
    cited = set(PLACEHOLDER.findall(text))
    if not cited or cited - set(facts) or set(facts) - cited:
        return None
    if re.search(r"\d", PLACEHOLDER.sub("", text)):
        return None
    return _parts(sentences, facts)


REWRITE_SYSTEM = (
    "You reword the briefing at the top of an AI governance report for the named reader, sentence by sentence. "
    "Use every {{fact-id}} placeholder exactly once and never write a number yourself; the placeholders are replaced "
    "with the real figures. Every sentence must contain at least one placeholder. Add no sentence, cause, judgement or "
    "conclusion the draft does not state. Plain, calm, specific English."
)
REWRITE_SCHEMA = {"type": "object", "properties": {"sentences": {"type": "array", "items": {"type": "string"}}}, "required": ["sentences"], "additionalProperties": False}


async def briefing_with_model(complete: Any, conn: Any, model: Dict[str, Any]) -> Dict[str, Any]:
    """Ask the organisation's model to reword the template; keep the template unless the reply passes accept_rewrite.

    complete is the api layer's llm.complete(conn, system, user, schema), handed in by the route.
    """
    import json

    sentences, facts = _sentences(model)
    prompt = json.dumps({"reader": model["role"], "draft": sentences, "facts": {k: {"note": v["note"]} for k, v in facts.items()}})
    try:
        data, _ = await complete(conn, REWRITE_SYSTEM, prompt, REWRITE_SCHEMA)
    except Exception:  # any provider failure keeps the template
        return {"source": "template", "parts": _parts(sentences, facts)}
    parts = accept_rewrite(data.get("sentences") or [], facts, len(sentences))
    return {"source": "model", "parts": parts} if parts else {"source": "template", "parts": _parts(sentences, facts)}
