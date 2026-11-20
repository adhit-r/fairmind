"""EU AI Act Art 5(1)(a)-(h) prohibited-practice screening, from a person's answers.

A screening aid, not a legal conclusion. Each prohibition becomes one plain question answered yes, no or unsure.
The result is deliberately conservative and never claims a system is lawful:

  indicated           at least one "yes": the practice may be prohibited. Stop and take it to legal counsel.
  needs_legal_review  no "yes", but an answer is "unsure" or missing: the screen cannot conclude.
  clear               every question answered "no". Self-attested; it says the answers found no prohibition,
                      not that the system complies.

Several prohibitions have narrow exceptions (for example medical or safety uses of emotion recognition, and the
law-enforcement limits on real-time biometric identification). The question notes name them so counsel can weigh them;
the rules here never apply an exception on their own.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

RULES_VERSION = "2026-11.1"
FRAMEWORK = "EUAIA"
ANSWERS = ("yes", "no", "unsure")

PROHIBITIONS = (
    ("a", "Art 5(1)(a)", "Subliminal, manipulative or deceptive techniques",
     "Does the system use subliminal, purposefully manipulative or deceptive techniques that materially distort people's behaviour and are likely to cause significant harm?",
     None),
    ("b", "Art 5(1)(b)", "Exploiting vulnerabilities",
     "Does the system exploit vulnerabilities of people because of their age, disability or social or economic situation, in a way likely to cause significant harm?",
     None),
    ("c", "Art 5(1)(c)", "Social scoring",
     "Does the system score or classify people over time by their social behaviour or personal traits, leading to harmful treatment in unrelated contexts or treatment that is unjustified or disproportionate?",
     None),
    ("d", "Art 5(1)(d)", "Crime prediction from profiling alone",
     "Does the system predict that a person will commit a crime based only on profiling or personality traits?",
     "Not covered: support for a human assessment that rests on objective, verifiable facts linked to criminal activity."),
    ("e", "Art 5(1)(e)", "Untargeted facial image scraping",
     "Does the system build or extend facial recognition databases by untargeted scraping of facial images from the internet or CCTV?",
     None),
    ("f", "Art 5(1)(f)", "Emotion recognition at work or in education",
     "Does the system infer people's emotions in the workplace or in education?",
     "Exception: systems intended for medical or safety reasons."),
    ("g", "Art 5(1)(g)", "Biometric categorisation of sensitive traits",
     "Does the system categorise people from biometric data to infer race, political opinions, trade union membership, religious or philosophical beliefs, sex life or sexual orientation?",
     "Not covered: labelling or filtering lawfully acquired biometric datasets, and some law-enforcement categorisation."),
    ("h", "Art 5(1)(h)", "Real-time remote biometric identification for law enforcement",
     "Does the system identify people in real time at a distance from biometric data in publicly accessible spaces for law enforcement?",
     "Narrow exceptions apply to defined objectives and need prior authorisation."),
)
KEYS = tuple(p[0] for p in PROHIBITIONS)


def questions() -> List[Dict[str, Any]]:
    return [{"key": k, "clause": c, "title": t, "question": q, "note": n} for k, c, t, q, n in PROHIBITIONS]


def screen(answers: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Screen a {key: yes|no|unsure} map. Unknown keys and unknown values are rejected, not ignored."""
    answers = answers or {}
    unknown = sorted(set(answers) - set(KEYS))
    if unknown:
        raise ValueError(f"Unknown prohibition keys: {', '.join(unknown)}")
    bad = sorted(k for k, v in answers.items() if v not in ANSWERS)
    if bad:
        raise ValueError(f"Answers must be yes, no or unsure: {', '.join(bad)}")
    rows, indicated, open_ = [], [], []
    for key, clause, title, _, _ in PROHIBITIONS:
        answer = answers.get(key)
        rows.append({"key": key, "clause": clause, "title": title, "answer": answer})
        if answer == "yes":
            indicated.append(clause)
        elif answer != "no":
            open_.append(clause)
    outcome = "indicated" if indicated else "needs_legal_review" if open_ else "clear"
    return {
        "rulesVersion": RULES_VERSION,
        "framework": FRAMEWORK,
        "outcome": outcome,
        "indicated": indicated,
        "open": open_,
        "answers": rows,
        "summary": {
            "indicated": f"May fall under {', '.join(indicated)}. Stop and take this to legal counsel before deployment.",
            "needs_legal_review": f"Cannot conclude: {', '.join(open_)} {'is' if len(open_) == 1 else 'are'} unanswered or unsure. Legal counsel should review.",
            "clear": "No prohibition was indicated by these answers. This is self-attested and is not a finding of compliance.",
        }[outcome],
    }
