"""FairMind sandbox runner: one evaluation per container, tar in on stdin, one JSON line out on stdout.

The launcher (apps/backend/src/infrastructure/sandbox/launcher.py) starts this with no network, a
read-only root and no arguments. stdin carries an uncompressed tar holding exactly:

  request.json        {"v": 1, "engine": "EV-TST-01", "params": {...}}
  inputs/<slot>       one regular file per slot the engine declares

Anything else (links, directories, unknown or repeated names, oversize members) is refused.
stdout carries exactly one line, either
  {"v":1,"engine":"EV-TST-01","status":"passed|failed|insufficient","metrics":{...}}
or
  {"v":1,"error":"<code>"}
Per-row detail and free-text summaries never leave the sandbox: they can carry labels from the data.
"""

import io
import json
import math
import os
import sys
import tarfile

MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024
MAX_PARAM_TEXT = 256

# The static engine map: engine id -> the metrics allowed out of the sandbox.
METRICS = {
    "EV-TST-01": frozenset(
        {"rows", "metric", "value", "accuracy", "macroF1", "mae", "rmse", "r2", "baseline", "lastRelease", "dropVsLastRelease"}
    ),
}


class Refused(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _engine(engine_id):
    if engine_id not in METRICS:
        raise Refused("unsupported_engine")
    from fairmind_engines import model  # the PR 261 engine code, copied in at build time

    return next(e for e in model.ENGINES if e.id == engine_id)


def _read_tar(raw):
    if len(raw) > MAX_INPUT_BYTES:
        raise Refused("input_too_large")
    members = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
            for info in archive:
                if not info.isreg() or info.name in members or info.size > MAX_INPUT_BYTES:
                    raise Refused("input_invalid")
                if info.name != "request.json" and not info.name.startswith("inputs/"):
                    raise Refused("input_invalid")
                members[info.name] = archive.extractfile(info).read()
    except (tarfile.TarError, EOFError):
        raise Refused("input_invalid")
    return members


def _param(value):
    if value is None or (isinstance(value, str) and len(value) <= MAX_PARAM_TEXT):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return value
    raise Refused("input_invalid")


def evaluate(raw):
    members = _read_tar(raw)
    try:
        request = json.loads(members.pop("request.json").decode("utf-8"))
    except (KeyError, ValueError):
        raise Refused("input_invalid")
    if not isinstance(request, dict) or set(request) != {"v", "engine", "params"} or request["v"] != 1:
        raise Refused("input_invalid")
    engine = _engine(request["engine"])
    params = request["params"]
    allowed_params = {p.name for p in engine.params}
    if not isinstance(params, dict) or not set(params) <= allowed_params:
        raise Refused("input_invalid")
    slots = {s.name for s in engine.slots}
    files = {name[len("inputs/"):]: data for name, data in members.items()}
    if not set(files) <= slots or any(s.required and s.name not in files for s in engine.slots):
        raise Refused("input_invalid")

    from fairmind_engines.common import EngineError

    try:
        outcome = engine.run(files, {k: _param(v) for k, v in params.items()})
    except Refused:
        raise
    except EngineError:
        raise Refused("input_invalid")
    except Exception:
        raise Refused("engine_failed")
    allowed = METRICS[engine.id]
    metrics = {k: v for k, v in outcome["metrics"].items() if k in allowed}
    return {"v": 1, "engine": engine.id, "status": outcome["status"], "metrics": metrics}


def _line(payload):
    return (json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def main():
    out = os.fdopen(os.dup(1), "wb")
    os.dup2(2, 1)  # anything a library prints goes to stderr, which the launcher discards
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        line = _line(evaluate(raw))
    except Refused as refused:
        line = _line({"v": 1, "error": refused.code})
    except ValueError:  # a non-finite metric: allow_nan=False refuses it
        line = _line({"v": 1, "error": "engine_failed"})
    if len(line) > MAX_OUTPUT_BYTES:
        line = _line({"v": 1, "error": "output_too_large"})
    out.write(line)
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
