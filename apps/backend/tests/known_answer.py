"""Shared helpers for the known-answer (maturity L4) engine tests.

Every known-answer test names the evaluations it validates with @known_answer("EV-...") and the path it
runs (eval_engines.paths); no path means the evaluation's main engine path. tests/test_known_answer_coverage.py
checks the evaluations covered on every path against eval_engines.VALIDATED, which is what the catalogue
export reads to record maturity L4.
"""

import io

import pandas as pd

COVERED = set()


def known_answer(*evaluation_ids, path=None):
    def mark(fn):
        COVERED.update((e, path) for e in evaluation_ids)
        return fn

    return mark


def csv(frame: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    frame.to_csv(buf, index=False)
    return buf.getvalue().encode()


def rows_csv(header, rows) -> bytes:
    return csv(pd.DataFrame(rows, columns=header))


def clause_judge(*absent, skip=()):
    """A fixed judge for EV-DEV-01: every clause the engine asks about is present except those in absent; skip gets no verdict."""
    def judge(system, user, schema):
        names = [line[2:].split(":")[0] for line in user.split("<clauses>\n")[1].split("\n</clauses>")[0].split("\n")]
        return {"clauses": [{"clause": n, "present": n not in absent, "quote": "" if n in absent else "given"} for n in names if n not in skip]}
    return judge
