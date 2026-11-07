"""The developer's signed-in Grok CLI as a model provider, for local development only.

The CLI is an agent with shell, file and web tools, and FairMind's prompts carry untrusted text
(customer model outputs, uploaded content). So every call offers the model no tools, denies every
tool call, stops after one turn, turns web search off, runs in the strict sandbox inside an empty
temporary directory with stdin closed, and is killed as soon as its output shows a tool on offer or
in use. It also runs with a grok home FairMind owns, holding only a copy of the developer's login, so
none of the developer's hooks, plugins, MCP servers, skills or rules load and no transcript is kept.
"""

import asyncio
import contextlib
import functools
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from config.settings import settings

TIMEOUT_S = 120
DEFAULT_SYSTEM = "Answer the user's message directly."
# What the CLI process may see of FairMind's environment, never DATABASE_URL or keys. HOME and GROK_HOME are FairMind's own.
ENV_KEEP = ("PATH", "USER", "LANG", "TMPDIR")
LINE_LIMIT = 16 * 1024 * 1024  # one streamed event carries a whole message
TOOL_BLOCKS = ("tool_use", "server_tool_use")
_MODEL_LINE = re.compile(r"^\s*([*-])\s+(\S+)")


class GrokCliError(Exception):
    """A failure the developer running FairMind can act on. Never carries the prompt."""


def enabled() -> bool:
    return settings.grok_cli_enabled and settings.is_development and shutil.which("grok") is not None


def _require_enabled() -> str:
    if not enabled():
        raise GrokCliError("The Grok CLI is not enabled on this server")
    return shutil.which("grok")


def _trim(raw: bytes) -> str:
    return " ".join(raw.decode(errors="replace").split())[-300:]


def _read(path: Path) -> Optional[bytes]:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _put(path: Path, data: bytes) -> None:
    """Write a login file owner-only, replacing what is there in one step."""
    fd, part = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")  # mkstemp makes it 0600
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(part, path)


@contextlib.contextmanager
def _isolated() -> Iterator[Tuple[dict, str, str]]:
    """One run's environment, empty working directory and private root.

    The grok home is a real directory (the strict sandbox refuses a symlinked one) holding only a copy
    of the developer's auth.json. If the CLI refreshes that login during the run, the new one goes back
    to the developer's file, unless that file changed meanwhile, so a rotated refresh token is not lost.
    """
    login = Path(os.environ.get("GROK_HOME") or Path.home() / ".grok") / "auth.json"
    with tempfile.TemporaryDirectory(prefix="fairmind-grok-") as root:
        home, cwd = Path(root, "home"), Path(root, "work")
        own = home / ".grok"
        own.mkdir(parents=True)
        cwd.mkdir()
        before = _read(login)
        if before is not None:
            _put(own / "auth.json", before)
        env = {k: os.environ[k] for k in ENV_KEEP if k in os.environ}
        env.update(HOME=str(home), GROK_HOME=str(own))
        try:
            yield env, str(cwd), root
        finally:
            after = _read(own / "auth.json")
            # ponytail: compare-then-replace leaves a moment in which a grok the developer runs could refresh too; one of the two wins.
            if before is not None and after and after != before and _read(login) == before:
                _put(login, after)


def models() -> List[str]:
    """The models `grok models` lists, the CLI's default first."""
    return _listed(_require_enabled())


@functools.lru_cache(maxsize=1)
def _listed(grok: str) -> List[str]:
    """Cached per process; a failure is not cached, so signing in and retrying works."""
    with _isolated() as (env, cwd, _):
        try:
            done = subprocess.run([grok, "models"], cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
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


def argv(grok: str, prompt_file: str, model: str, system: Optional[str], cwd: str) -> List[str]:
    """The locked-down call. Every value rides --flag=value, so a value that starts with "-" is never read as a flag.

    The prompt comes from a file in the run's private root, so it is not on the command line for `ps` to show.
    """
    return [
        grok,
        f"--prompt-file={prompt_file}",
        f"--model={model}",
        f"--system-prompt-override={system or DEFAULT_SYSTEM}",
        "--verbatim",  # no @file or slash-command expansion of the prompt
        # An empty or unknown --tools entry offers every tool, so allow one and then remove it with the
        # MCP meta-tools; the CLI then reports an empty toolset, which _watch checks.
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
        "--include-partial-messages",  # a tool block shows as it starts, not once the message is done
    ]


async def _watch(proc: asyncio.subprocess.Process) -> str:
    """The final text, read as the CLI prints it. Raises, and so stops the run, at the first event that is
    not preceded by the CLI's report of an empty toolset, or that shows a tool block."""
    tools, text = None, ""
    try:
        async for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if kind == "system" and event.get("subtype") == "init":
                tools = event.get("tools")
            if tools != []:
                raise GrokCliError("The Grok CLI did not confirm an empty toolset; the call was stopped")
            if kind == "assistant":
                blocks = (event.get("message") or {}).get("content") or []
            elif kind == "stream_event" and (event.get("event") or {}).get("type") == "content_block_start":
                blocks = [event["event"].get("content_block")]
            else:
                blocks = []
            if any(isinstance(b, dict) and b.get("type") in TOOL_BLOCKS for b in blocks):
                raise GrokCliError("The model tried to use a tool; the call was stopped")
            if kind == "result":
                if event.get("is_error"):
                    raise GrokCliError(f"The Grok CLI stopped: {event.get('subtype') or 'error'}")
                text = event.get("result") or ""
    except ValueError:  # a line past LINE_LIMIT
        raise GrokCliError("The Grok CLI printed more than FairMind reads") from None
    await proc.wait()
    return text


async def complete(prompt: str, model: str, system: Optional[str] = None, timeout: float = TIMEOUT_S) -> str:
    grok = _require_enabled()
    with _isolated() as (env, cwd, root), tempfile.TemporaryFile(dir=root) as err:
        prompt_file = Path(root, "prompt")
        prompt_file.write_bytes(prompt.encode("utf-8", "replace"))
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv(grok, str(prompt_file), model, system, cwd),
                cwd=cwd,
                env=env,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=err,
                limit=LINE_LIMIT,
            )
        except (OSError, ValueError) as e:
            raise GrokCliError(f"Could not start the Grok CLI: {getattr(e, 'strerror', None) or type(e).__name__}") from None
        try:
            text = await asyncio.wait_for(_watch(proc), timeout)
        except asyncio.TimeoutError:
            raise GrokCliError("The Grok CLI did not answer in time") from None
        finally:
            if proc.returncode is None:  # stopped by _watch, timed out, or the request was cancelled
                proc.kill()
                await proc.wait()
        if proc.returncode != 0:
            err.seek(0)
            raise GrokCliError(f"The Grok CLI failed (exit {proc.returncode}): {_trim(err.read()) or 'no detail'}")
    if not text.strip():
        raise GrokCliError("The Grok CLI returned an empty answer")
    return text
