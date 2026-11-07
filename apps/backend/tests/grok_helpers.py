"""A fake `grok` executable for tests, so no test ever runs the real Grok CLI.

It records each call (argv, working directory and its files, whether stdin is /dev/null, the
environment's names, its pid) as one JSON line, then answers like the CLI does.
"""

import json
import os
import sys
from pathlib import Path

from config.settings import settings
from src.infrastructure.llm import grok_cli

LISTING = "You are logged in with grok.com.\n\nDefault model: grok-4.7\n\nAvailable models:\n  - grok-4.6\n  * grok-4.7 (default)\n  - grok-4.5\n"


def stream(text: str, tools=(), tool_use: bool = False) -> str:
    """What `--output-format=streaming-messages-json` prints for one answer."""
    content = [{"type": "tool_use", "id": "call_1", "name": "run_terminal_command", "input": {}}] if tool_use else []
    events = [
        {"type": "system", "subtype": "init", "tools": list(tools), "permissionMode": "dontAsk"},
        {"type": "assistant", "message": {"content": content + [{"type": "text", "text": text}]}},
        {"type": "result", "subtype": "success", "is_error": False, "result": text, "stop_reason": "end_turn"},
    ]
    return "".join(json.dumps(e) + "\n" for e in events)


def fake_grok(monkeypatch, tmp_path: Path, *, out: str | None = None, listing: str = LISTING, run: str = "") -> Path:
    """Put a fake grok first on PATH and switch the CLI on; returns the file its calls are recorded in.

    `run` is Python the fake runs after recording, before it answers (sleep, exit with an error).
    """
    calls = tmp_path / "grok-calls.jsonl"
    exe = tmp_path / "bin" / "grok"
    exe.parent.mkdir(exist_ok=True)
    answer = stream('{"ok": true}') if out is None else out
    exe.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys, time\n"
        f"with open({str(calls)!r}, 'a') as f:\n"
        "    f.write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'files': os.listdir('.'),\n"
        "        'stdin_devnull': os.path.samestat(os.fstat(0), os.stat(os.devnull)), 'env': sorted(os.environ), 'pid': os.getpid()}) + '\\n')\n"
        f"{run}\n"
        f"sys.stdout.write({listing!r} if sys.argv[1:] == ['models'] else {answer!r})\n"
    )
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", f"{exe.parent}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(settings, "grok_cli_enabled", True)
    monkeypatch.setattr(settings, "environment", "development")
    grok_cli._listed.cache_clear()
    return calls


def recorded(calls: Path) -> list:
    return [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []
