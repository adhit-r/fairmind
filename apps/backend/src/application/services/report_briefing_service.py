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
        out.append(f"{f.add('tasks.open', str(tasks['open']), 'Open tasks')} tasks are open and {f.add('tasks.overdue', str(tasks['overdue']), 'Tasks past their due date', 'bad' if tasks['overdue'] else '')} are overdue.")
    cross = model.get("crosswalk")
    other = next((x for x in (cross or {}).get("frameworks", []) if not x["followed"]), None)
    if other:
        out.append(f"Evidence you hold already covers {f.add('crosswalk.top', str(other['coverage']) + '%', 'Clauses covered through the clause map')} of {other['name']}.")
    systems = model.get("systems")
    if systems is not None:
        failing = [s for s in systems if any(c["fails"] for c in s["checks"])]
        out.append(f"{f.add('systems.failing', str(len(failing)), 'Systems with a failing gate check', 'bad' if failing else '')} "
                   f"{_plural(len(failing), 'system fails', 'systems fail')} a release gate check.")
    eng = model.get("engineering")
    if eng:
        ungated = [t for t in eng["toolExposure"] if not t["gated"]]
        if eng["toolExposure"]:
            out.append(f"{f.add('tools.ungated', str(len(ungated)), 'High-risk agent tools that run without a person approving', 'bad' if ungated else '')} high-risk agent "
                       f"{_plural(len(ungated), 'tool runs', 'tools run')} without a person approving each call.")
    aud = model.get("auditor")
    if aud:
        ledger = aud["ledger"]
        out.append(f"The ledger holds {f.add('ledger.entries', str(ledger['entries']), 'Hash-chained entries across workflow runs, internal audits and seals')} entries and is "
                   f"{f.add('ledger.state', 'intact' if ledger['intact'] else 'broken', 'Every chain recomputed just now', '' if ledger['intact'] else 'bad')}.")
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


def accept_rewrite(sentences: List[str], facts: Dict[str, Dict[str, Any]]) -> Optional[List[Part]]:
    """The model's sentences, or None when they cite an unknown fact, drop a fact or write a digit of their own."""
    if not sentences or not all(isinstance(s, str) for s in sentences):
        return None
    text = " ".join(sentences)
    cited = set(PLACEHOLDER.findall(text))
    if not cited or cited - set(facts) or set(facts) - cited:
        return None
    if re.search(r"\d", PLACEHOLDER.sub("", text)):
        return None
    return _parts(sentences, facts)


REWRITE_SYSTEM = (
    "You write the two-to-four sentence briefing at the top of an AI governance report for the named reader. "
    "Use every {{fact-id}} placeholder exactly once and never write a number yourself; the placeholders are replaced "
    "with the real figures. Plain, calm, specific English. No advice the facts do not support."
)
REWRITE_SCHEMA = {"type": "object", "properties": {"sentences": {"type": "array", "items": {"type": "string"}}}, "required": ["sentences"], "additionalProperties": False}


async def briefing_with_model(conn: Any, model: Dict[str, Any]) -> Dict[str, Any]:
    """Ask the organisation's model to reword the template; keep the template unless the reply passes accept_rewrite."""
    import json

    from api.routes import llm

    sentences, facts = _sentences(model)
    prompt = json.dumps({"reader": model["role"], "draft": sentences, "facts": {k: {"note": v["note"]} for k, v in facts.items()}})
    try:
        data, _ = await llm.complete(conn, REWRITE_SYSTEM, prompt, REWRITE_SCHEMA)
    except Exception:  # any provider failure keeps the template
        return {"source": "template", "parts": _parts(sentences, facts)}
    parts = accept_rewrite(data.get("sentences") or [], facts)
    return {"source": "model", "parts": parts} if parts else {"source": "template", "parts": _parts(sentences, facts)}
