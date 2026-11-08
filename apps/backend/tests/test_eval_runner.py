"""apps/eval-runner/runner.py: the tar it accepts, what it refuses and the one line it writes.

The image copies eval_engines/common.py and model.py in as fairmind_engines; this test aliases
the backend package to that name so the same code runs here without Docker.
"""

import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

from src.application.services.eval_engines import common, model

sys.modules.setdefault("fairmind_engines", sys.modules["src.application.services.eval_engines"])
sys.modules.setdefault("fairmind_engines.common", common)
sys.modules.setdefault("fairmind_engines.model", model)

_spec = importlib.util.spec_from_file_location(
    "eval_runner", Path(__file__).resolve().parents[2] / "eval-runner" / "runner.py"
)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

CSV = b"y_true,y_pred\nalice,alice\nbob,bob\nalice,bob\nbob,bob\n"
REQUEST = {"v": 1, "engine": "EV-TST-01", "params": {"baseline": 0.7}}


def tar(*members):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, data, kind in members:
            info = tarfile.TarInfo(name)
            info.type = kind
            if kind == tarfile.SYMTYPE:
                info.linkname = "/etc/passwd"
            else:
                info.size = len(data)
            archive.addfile(info, io.BytesIO(data) if kind == tarfile.REGTYPE else None)
    return buffer.getvalue()


def ok(request=REQUEST, csv=CSV):
    return [("request.json", json.dumps(request).encode(), tarfile.REGTYPE), ("inputs/predictions", csv, tarfile.REGTYPE)]


def test_runs_ev_tst_01_and_withholds_detail():
    result = runner.evaluate(tar(*ok()))
    assert result["status"] == "passed" and result["engine"] == "EV-TST-01"
    assert result["metrics"]["accuracy"] == 0.75
    assert set(result) == {"v", "engine", "status", "metrics"}
    # Class labels from the data never appear in the output.
    assert b"alice" not in runner._line(result) and b"bob" not in runner._line(result)


def test_output_line_passes_the_launcher_parser():
    from src.infrastructure.sandbox import parse_runner_output

    assert parse_runner_output(runner._line(runner.evaluate(tar(*ok()))))["status"] == "passed"


@pytest.mark.parametrize(
    "members, code",
    [
        (ok() + [("inputs/predictions", CSV, tarfile.REGTYPE)], "input_invalid"),  # repeated name
        (ok() + [("extra.txt", b"x", tarfile.REGTYPE)], "input_invalid"),
        (ok() + [("inputs/other", b"x", tarfile.REGTYPE)], "input_invalid"),  # undeclared slot
        (ok()[:1] + [("inputs/predictions", b"", tarfile.SYMTYPE)], "input_invalid"),
        (ok() + [("inputs/dir", b"", tarfile.DIRTYPE)], "input_invalid"),
        (ok()[:1], "input_invalid"),  # required slot missing
        (ok()[1:], "input_invalid"),  # no request
        (ok({**REQUEST, "engine": "EV-TST-02"}), "unsupported_engine"),
        (ok({**REQUEST, "params": {"command": "x"}}), "input_invalid"),
        (ok({**REQUEST, "params": {"baseline": True}}), "input_invalid"),
        (ok({**REQUEST, "params": {"y_true": "x" * 300}}), "input_invalid"),
        (ok({**REQUEST, "extra": 1}), "input_invalid"),
        (ok(csv=b"a,b\n1,2\n"), "input_invalid"),  # EngineError: missing columns
    ],
)
def test_refuses_anything_else(members, code):
    with pytest.raises(runner.Refused) as caught:
        runner.evaluate(tar(*members))
    assert caught.value.code == code


def test_refuses_non_tar_and_oversize_input(monkeypatch):
    with pytest.raises(runner.Refused):
        runner.evaluate(b"not a tar archive at all" * 100)
    monkeypatch.setattr(runner, "MAX_INPUT_BYTES", 10)
    with pytest.raises(runner.Refused) as caught:
        runner.evaluate(tar(*ok()))
    assert caught.value.code == "input_too_large"
