"""What every engine shares: its declaration, the result shape and input parsing."""

import io
import json
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

MAX_DETAIL_ROWS = 200


class EngineError(ValueError):
    """The inputs cannot be evaluated; the message tells the person what to fix."""


@dataclass(frozen=True)
class Slot:
    """A file the engine reads."""

    name: str
    label: str
    help: str
    kind: str = "csv"  # csv | text | json | binary
    required: bool = True


@dataclass(frozen=True)
class Param:
    """A setting the engine reads; columns are named in text params."""

    name: str
    label: str
    help: str
    kind: str = "text"  # text | number | json
    default: Any = None
    required: bool = False
    options: Tuple[str, ...] = ()  # a text param limited to these values, shown as a choice


# (system, user, JSON schema) -> the organisation's model's JSON answer; raises EngineError
Judge = Callable[[str, str, Dict[str, Any]], Dict[str, Any]]


def matches_schema(value: Any, schema: Dict[str, Any]) -> bool:
    """A judge's answer has every required key and the declared booleans, integers, arrays and objects; strings are only read with str()."""
    kind = schema.get("type")
    if kind == "object":
        props = schema.get("properties", {})
        return (isinstance(value, dict) and all(k in value for k in schema.get("required", ()))
                and all(matches_schema(value[k], sub) for k, sub in props.items() if k in value))
    if kind == "array":
        return isinstance(value, list) and all(matches_schema(v, schema.get("items", {})) for v in value)
    if kind == "boolean":
        return isinstance(value, bool)  # "false" is not false
    if kind == "integer":  # JSON Schema counts 2.0 as an integer
        return (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and value.is_integer())
    return True


@dataclass(frozen=True)
class Engine:
    id: str
    method: str  # one line on how the engine measures, shown beside the run form
    slots: Tuple[Slot, ...]
    # Reads the uploaded files: (files, params) -> result; live engines are async (files, params, Live) -> result.
    # None for an engine that only reads an agent platform's configuration, whose one slot is that
    # configuration exported as JSON.
    run: Optional[Callable[..., Any]] = None
    params: Tuple[Param, ...] = field(default_factory=tuple)
    # Reads an agent platform snapshot (platform.snapshot shape), from a connection or an export.
    platform: Optional[Callable[[Dict[str, Any], Dict[str, Any], Optional[Judge]], Dict[str, Any]]] = None
    platform_method: str = ""
    judge: bool = False  # the platform check asks the organisation's model
    file_judge: bool = False  # the file run takes the organisation's model as a third argument, None when none is set
    live: str = ""  # "" reads uploaded files; "target" calls the AI system under test; "agent" calls FairMind's own agent
    # Reads inputs from FairMind's own stored results: (db session, org id, system id) -> files, added to any uploads.
    collect: Optional[Callable[[Any, str, str], Dict[str, bytes]]] = None
    # A rate-bounded behaviour test: the probe counts the run form offers and the 95% bound each shows with none failing.
    sampling: Optional[Dict[str, Any]] = field(default=None, hash=False, compare=False)

    def spec(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "method": self.method,
            "slots": [s.__dict__ for s in self.slots],
            "params": [p.__dict__ for p in self.params],
            "live": self.live,
            "platform": self.platform is not None,
            "platformMethod": self.platform_method or self.method,
            "judge": self.judge,
            "fileJudge": self.file_judge,
            "sampling": self.sampling,
        }


def result(status: str, summary: str, metrics: Dict[str, Any], detail: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """status: passed, failed, or insufficient when the inputs cannot support a verdict."""
    assert status in ("passed", "failed", "insufficient")
    rows = detail or []
    return {"status": status, "summary": summary, "metrics": metrics, "detail": rows[:MAX_DETAIL_ROWS], "detailTotal": len(rows)}


# Evaluations whose catalogue threshold needs a person to review every flagged item (POST /evaluation-runs/{id}/reviews):
# decision -> whether it clears the item. The run passes once every item is cleared and fails once any is confirmed.
REVIEW_DECISIONS: Dict[str, Dict[str, bool]] = {
    "EV-DAT-02": {"benign": True, "poisoned": False},
    "EV-DAT-07": {"benign": True, "poisoned": False},
    "EV-DEV-03": {"resolved": True, "accepted": True},
}


def awaiting_review(measured: str, metrics: Dict[str, Any], detail: List[Dict[str, Any]], items: Dict[str, str]) -> Dict[str, Any]:
    """A run whose measurement is within the threshold but whose flagged items (key -> what it is) no person has reviewed yet."""
    n = len(items)
    out = result("insufficient", f"{measured} {n} flagged {'item awaits' if n == 1 else 'items await'} a person's review; "
                 "the run passes once every one is reviewed and cleared.", {**metrics, "unreviewed": n}, detail)
    out["review"] = {"measured": measured, "items": [{"item": k, "label": v} for k, v in items.items()]}
    return out


def reviewed(evaluation_id: str, items: List[str], decisions: Dict[str, str]) -> Tuple[str, int]:
    """The verdict on a run awaiting review, from each item's latest decision: failed once any decision confirms an item,
    insufficient while any item has none, else passed; with how many items are still unreviewed."""
    clears = REVIEW_DECISIONS[evaluation_id]
    left = sum(1 for i in items if i not in decisions)
    if any(not clears[decisions[i]] for i in items if i in decisions):
        return "failed", left
    return ("insufficient" if left else "passed"), left


def upper_bound(bad: int, n: int) -> float:
    """The one-sided 95% Clopper-Pearson upper bound on a rate seen as bad of n, as a fraction."""
    if bad >= n:
        return 1.0
    if bad == 0:
        return 1 - 0.05 ** (1 / n)

    def at_most(p: float) -> float:  # P(X <= bad) for X ~ Binomial(n, p), in logs so large n cannot overflow
        lp, lq, top = math.log(p), math.log1p(-p), math.lgamma(n + 1)
        return sum(math.exp(top - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq) for i in range(bad + 1))

    lo, hi = bad / n, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if at_most(mid) > 0.05 else (lo, mid)
    return hi


def sampled(status: str, bad: int, n: int, limit: float) -> Tuple[str, str]:
    """A pass stands only when the 95% upper bound on bad of n is within limit (a fraction); otherwise insufficient, with the sentence why."""
    if status != "passed" or not 0 < limit < 1 or n <= 0:  # a zero limit is zero tolerance: no sample bounds a rate at 0
        return status, ""
    high = upper_bound(bad, n)
    if high <= limit:
        return status, ""
    pct = f"{round(limit * 100, 4):g}%"
    return "insufficient", (f" {bad} of {n} is within {pct}, but at 95% confidence the rate could be as high as {high:.1%}, so this sample "
                            f"cannot show it is at or under {pct}; that takes at least {samples_needed(limit)} with none failing.")


def samples_needed(limit: float) -> int:
    """The smallest sample whose 95% upper bound is within limit (a fraction between 0 and 1) when nothing in it fails."""
    return math.ceil(math.log(0.05) / math.log(1 - limit))


def read_csv(raw: bytes, what: str, text: bool = False, literal: bool = False) -> pd.DataFrame:
    """text keeps every cell as a string, so ids and yes/no flags never turn into floats like 1.0 when a cell is blank.
    literal also keeps NA, None, null and the like as written, so only a blank cell is missing (a tool may be named NA)."""
    if not raw:
        raise EngineError(f"{what} is empty")
    try:
        frame = pd.read_csv(io.BytesIO(raw), dtype=str if text or literal else None, keep_default_na=not literal, na_values=[""] if literal else None)
    except Exception as exc:  # pandas raises several parser errors
        raise EngineError(f"{what} is not a readable CSV: {exc}")
    if frame.empty:
        raise EngineError(f"{what} has no rows")
    return frame


def read_text(raw: bytes, what: str) -> str:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise EngineError(f"{what} is not UTF-8 text")
    if not text.strip():
        raise EngineError(f"{what} is empty")
    return text


def read_json(raw: bytes, what: str) -> Any:
    try:
        return json.loads(read_text(raw, what))
    except ValueError as exc:
        raise EngineError(f"{what} is not valid JSON: {exc}")


def columns(frame: pd.DataFrame, names: List[str], what: str) -> None:
    missing = [n for n in names if n not in frame.columns]
    if missing:
        raise EngineError(f"{what} has no column {', '.join(missing)}; it has {', '.join(map(str, frame.columns[:20]))}")


def split(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def number(params: Dict[str, Any], name: str, default: float) -> float:
    value = params.get(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        raise EngineError(f"{name} must be a number")
