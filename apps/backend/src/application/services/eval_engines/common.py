"""What every engine shares: its declaration, the result shape and input parsing."""

import io
import json
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
    live: str = ""  # "" reads uploaded files; "target" calls the AI system under test; "agent" calls FairMind's own agent
    # Reads inputs from FairMind's own stored results: (db session, org id, system id) -> files, added to any uploads.
    collect: Optional[Callable[[Any, str, str], Dict[str, bytes]]] = None

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
        }


def result(status: str, summary: str, metrics: Dict[str, Any], detail: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """status: passed, failed, or insufficient when the inputs cannot support a verdict."""
    assert status in ("passed", "failed", "insufficient")
    rows = detail or []
    return {"status": status, "summary": summary, "metrics": metrics, "detail": rows[:MAX_DETAIL_ROWS], "detailTotal": len(rows)}


def read_csv(raw: bytes, what: str) -> pd.DataFrame:
    if not raw:
        raise EngineError(f"{what} is empty")
    try:
        frame = pd.read_csv(io.BytesIO(raw))
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
