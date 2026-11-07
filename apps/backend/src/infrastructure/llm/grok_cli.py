"""The developer's signed-in Grok CLI as a model provider, for local development only.

The CLI is an agent with shell, file and web tools, and FairMind's prompts carry untrusted text
(customer model outputs, uploaded content). So every call offers the model no tools, denies every
tool call, stops after one turn, turns web search off, runs in the strict sandbox inside an empty
temporary directory with stdin closed, and its answer is discarded unless the CLI reports that the
session had no tools.
"""

import asyncio
import functools
import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import List, Optional

from config.settings import settings

TIMEOUT_S = 120
DEFAULT_SYSTEM = "Answer the user's message directly."
# What the CLI process may see of FairMind's environment: enough to find its login, never DATABASE_URL or keys.
ENV_KEEP = ("PATH", "HOME", "USER", "LANG", "TMPDIR", "GROK_HOME")
_MODEL_LINE = re.compile(r"^\s*([*-])\s+(\S+)")


class GrokCliError(Exception):
    """A failure the developer running FairMind can act on. Never carries the prompt."""


def enabled() -> bool:
    return settings.grok_cli_enabled and settings.environment != "production" and shutil.which("grok") is not None


def _require_enabled() -> str:
    if not enabled():
        raise GrokCliError("The Grok CLI is not enabled on this server")
    return shutil.which("grok")


def _env() -> dict:
    return {k: os.environ[k] for k in ENV_KEEP if k in os.environ}


def _trim(raw: bytes) -> str:
    return " ".join(raw.decode(errors="replace").split())[-300:]


def models() -> List[str]:
    """The models `grok models` lists, the CLI's default first."""
    return _listed(_require_enabled())


@functools.lru_cache(maxsize=1)
def _listed(grok: str) -> List[str]:
    """Cached per process; a failure is not cached, so signing in and retrying works."""
    with tempfile.TemporaryDirectory(prefix="fairmind-grok-") as cwd:
        try:
            done = subprocess.run([grok, "models"], cwd=cwd, env=_env(), stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
        except subprocess.TimeoutExpired:
            raise GrokCliError("The Grok CLI did not list its models in time")
    out = done.stdout.decode(errors="replace")
    if "not authenticated" in (out + done.stderr.decode(errors="replace")).lower():
        raise GrokCliError("The Grok CLI is not signed in; run grok login")
    if done.returncode != 0:
        raise GrokCliError(f"grok models failed (exit {done.returncode}): {_trim(done.stderr)}")
    found = [(m.group(2), m.group(1) == "*") for m in map(_MODEL_LINE.match, out.splitlines()) if m]
    if not found:
        raise GrokCliError("The Grok CLI listed no models")
    return [name for name, _ in sorted(found, key=lambda f: not f[1])]


def argv(grok: str, prompt: str, model: str, system: Optional[str], cwd: str) -> List[str]:
    """The locked-down call. Every value rides --flag=value, so a prompt that starts with "-" is never read as a flag."""
    # ponytail: the prompt rides argv, which caps one argument at 128 KiB on Linux and all of argv plus env
    # at about 1 MiB on macOS (E2BIG past that). Write it to a file in cwd and pass --prompt-file if prompts outgrow it.
    return [
        grok,
        f"--single={prompt}",
        f"--model={model}",
        f"--system-prompt-override={system or DEFAULT_SYSTEM}",
        "--verbatim",  # no @file or slash-command expansion of the prompt
        # An empty or unknown --tools entry offers every tool, so allow one and then remove it with the
        # MCP meta-tools; the CLI then reports an empty toolset, which _answer checks.
        "--tools=todo_write",
        "--disallowed-tools=todo_write,use_tool,search_tool,Agent",
        "--deny=*",
        "--permission-mode=dontAsk",
        "--max-turns=1",
        "--disable-web-search",
        "--no-subagents",
        "--sandbox=strict",
        f"--cwd={cwd}",
        "--output-format=streaming-messages-json",
    ]


def _answer(stdout: bytes) -> str:
    """The final text, only from a session that had no tools and used none."""
    tools, text = None, ""
    for line in stdout.decode(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            tools = event.get("tools")
        elif event.get("type") == "assistant":
            blocks = (event.get("message") or {}).get("content") or []
            if any(isinstance(b, dict) and b.get("type") in ("tool_use", "server_tool_use") for b in blocks):
                raise GrokCliError("The model tried to use a tool; its answer was discarded")
        elif event.get("type") == "result":
            if event.get("is_error"):
                raise GrokCliError(f"The Grok CLI stopped: {event.get('subtype') or 'error'}")
            text = event.get("result") or ""
    if tools != []:
        raise GrokCliError("The Grok CLI did not confirm an empty toolset; its answer was discarded")
    if not text.strip():
        raise GrokCliError("The Grok CLI returned an empty answer")
    return text


async def complete(prompt: str, model: str, system: Optional[str] = None, timeout: float = TIMEOUT_S) -> str:
    grok = _require_enabled()
    with tempfile.TemporaryDirectory(prefix="fairmind-grok-") as cwd:
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv(grok, prompt, model, system, cwd),
                cwd=cwd,
                env=_env(),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except (OSError, ValueError) as e:  # E2BIG for an oversized prompt, ValueError for a NUL byte
            raise GrokCliError(f"Could not start the Grok CLI: {getattr(e, 'strerror', None) or type(e).__name__}") from None
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            raise GrokCliError("The Grok CLI did not answer in time") from None
        finally:
            if proc.returncode is None:  # timed out or the request was cancelled
                proc.kill()
                await proc.wait()
    if proc.returncode != 0:
        raise GrokCliError(f"The Grok CLI failed (exit {proc.returncode}): {_trim(err) or 'no detail'}")
    return _answer(out)
