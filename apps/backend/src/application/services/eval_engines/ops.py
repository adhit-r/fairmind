"""Engines that read prompts, configuration and logs: system prompts, secrets, model files, tools, MCP, agents, cost and logs."""

import csv
import io
import json
import pickletools
import re
import zipfile
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

import pandas as pd

from .common import Engine, EngineError, Param, Slot, columns, number, read_csv, read_json, read_text, result, split
from .detectors import INSTRUCTIONS, PERSONAL, SECRETS, mask, scan

SNIPPET = 120


def _scrub(text: str, limit: int = SNIPPET) -> str:
    """Text safe to show: any secret inside is masked before the text is cut."""
    for _, value in scan(text, SECRETS):
        text = text.replace(value, mask(value))
    return text if len(text) <= limit else text[:limit] + "..."


def _pct(part: int, whole: int) -> str:
    return f"{part / whole:.0%}" if whole else "0%"


# --- EV-DEV-01 system prompt safety instructions ------------------------------------------------

CLAUSES: Dict[str, List[str]] = {
    "role": [r"\byou are\b", r"\byour (?:role|job|task|purpose) is\b", r"\bact as\b", r"\byou will (?:act|serve|work) as\b"],
    "scope": [r"\bonly\b", r"\b(?:do not|don't|never) (?:answer|respond|help|discuss)\b", r"\bout of scope\b", r"\bdecline\b",
              r"\brefuse\b", r"\bmust not\b", r"\bwill not\b"],
    "override resistance": [r"\bignore (?:any|all)\b.{0,50}\b(?:instructions?|requests?|attempts?)\b", r"\b(?:do not|don't|never) (?:reveal|disclose|share|repeat)\b",
                            r"\buntrusted\b", r"\b(?:cannot|can't|must not|never) be (?:changed|overridden|overruled)\b",
                            r"\b(?:do not|don't|never) follow (?:any )?instructions\b"],
}


def _extra_clauses(value: Any) -> Dict[str, List[str]]:
    if value in (None, "", []):
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as exc:
            raise EngineError(f"extra_clauses is not valid JSON: {exc}")
    if not isinstance(value, list) or not all(isinstance(c, dict) and c.get("name") and c.get("pattern") for c in value):
        raise EngineError('extra_clauses must be a JSON list of {"name": ..., "pattern": ...} objects')
    return {str(c["name"]): [str(c["pattern"])] for c in value}


def system_prompt(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    text = read_text(files["system_prompt"], "The system prompt")
    clauses = {**CLAUSES, **_extra_clauses(params.get("extra_clauses"))}
    rows = []
    for name, patterns in clauses.items():
        try:
            match = re.search("|".join(f"(?:{p})" for p in patterns), text, re.I | re.S)
        except re.error as exc:
            raise EngineError(f"The pattern for clause '{name}' is not a valid regex: {exc}")
        rows.append({"clause": name, "present": bool(match), "matched": _scrub(match.group(0), 80) if match else ""})
    missing = [r["clause"] for r in rows if not r["present"]]
    present = len(rows) - len(missing)
    metrics = {"requiredClauses": len(rows), "present": present, "missing": len(missing), "coverage": round(present / len(rows), 4)}
    if missing:
        summary = f"{present} of {len(rows)} required clauses are present ({_pct(present, len(rows))}); missing: {', '.join(missing)}."
    else:
        summary = f"All {len(rows)} required clauses are present."
    return result("failed" if missing else "passed", summary, metrics, rows)


# --- EV-DEV-02 / EV-SEC-16 secrets ---------------------------------------------------------------

def _line_hits(text: str, detectors, kind: str) -> List[Dict[str, Any]]:
    return [{"kind": kind, "line": no, "category": cat, "value": mask(val)}
            for no, line in enumerate(text.splitlines(), 1) for cat, val in scan(line, detectors)]


def file_secrets(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    text = read_text(files["file"], "The file")
    rows = _line_hits(text, SECRETS, "secret")
    by = Counter(r["category"] for r in rows)
    metrics = {"lines": len(text.splitlines()), "secrets": len(rows), "byCategory": dict(by)}
    if not rows:
        return result("passed", f"No secrets found in {metrics['lines']} lines.", metrics)
    cats = ", ".join(f"{n} {c}" for c, n in by.most_common(4))
    return result("failed", f"{len(rows)} secrets found ({cats}); first on line {rows[0]['line']}. Rotate them and load them from a secret store.", metrics, rows)


def context_secrets(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    text = read_text(files["context"], "The context export")
    secrets = _line_hits(text, SECRETS, "secret")
    personal = _line_hits(text, PERSONAL, "personal")
    metrics = {"lines": len(text.splitlines()), "secrets": len(secrets), "personalData": len(personal),
               "secretsByCategory": dict(Counter(r["category"] for r in secrets)),
               "personalByCategory": dict(Counter(r["category"] for r in personal))}
    note = f" It also holds {len(personal)} personal-data hits, reported but not counted against the check." if personal else ""
    rows = secrets + personal
    if not secrets:
        return result("passed", f"No secrets found in {metrics['lines']} lines of agent context.{note}", metrics, rows)
    return result("failed", f"{len(secrets)} secrets found in agent context; first on line {secrets[0]['line']}.{note}", metrics, rows)


# --- EV-SEC-14 model file and dependency scanning ------------------------------------------------

DANGEROUS_MODULES = {"os", "posix", "nt", "subprocess", "sys", "socket", "shutil", "runpy", "pty", "webbrowser",
                     "importlib", "ctypes", "pickle", "marshal"}
DANGEROUS_BUILTINS = {"eval", "exec", "getattr", "setattr", "delattr", "__import__", "compile", "open", "globals", "locals", "input", "breakpoint"}
NUMPY_MODULES = {"numpy", "numpy.core.multiarray", "numpy._core.multiarray", "numpy.core.numeric", "numpy._core.numeric", "numpy.dtypes"}
TORCH_STORAGE = {"TypedStorage", "_TypedStorage", "UntypedStorage"}
STRING_OPS = {"SHORT_BINUNICODE", "BINUNICODE", "BINUNICODE8", "UNICODE", "SHORT_BINSTRING", "BINSTRING", "STRING"}
MAX_MEMBER = 256 * 1024 * 1024


class _NotPickle(Exception):
    pass


def _import_risk(module: str, name: str) -> Optional[str]:
    """high for known-dangerous imports, medium for anything off the allowlist, None when safe."""
    if module.split(".")[0] in DANGEROUS_MODULES or (module in ("builtins", "__builtin__") and name in DANGEROUS_BUILTINS):
        return "high"
    safe = (
        (module in ("builtins", "__builtin__") and name in {"set", "frozenset", "slice", "complex"})
        or module == "collections"
        or module in NUMPY_MODULES
        or module.split(".")[0] == "sklearn"  # ponytail: whole sklearn trusted; narrow to estimator modules if needed
        or (module == "torch" and (name.endswith("Storage") or name == "Size"))
        or (module == "torch._utils" and name.startswith("_rebuild"))
        or (module == "torch.storage" and name in TORCH_STORAGE)
    )
    return None if safe else "medium"


def _pickle_findings(data: bytes) -> List[Tuple[str, str, str]]:
    """(finding, import, severity) from the opcodes alone; the pickle is never loaded.

    STACK_GLOBAL names are only trusted when the two strings were pushed directly before it, so a
    stream that hides its target behind other stack operations is reported as unresolved.
    """
    found: List[Tuple[str, str, str]] = []
    stream, opcodes, finished = io.BytesIO(data), 0, 0
    while stream.tell() < len(data):
        pending: List[Optional[str]] = []
        memo: Dict[int, Optional[str]] = {}
        try:
            for op, arg, _ in pickletools.genops(stream):
                opcodes += 1
                n = op.name
                if n in STRING_OPS:
                    pending.append(arg)
                elif n == "MEMOIZE":
                    memo[len(memo)] = pending[-1] if pending else None
                elif n in ("PUT", "BINPUT", "LONG_BINPUT"):
                    memo[arg] = pending[-1] if pending else None
                elif n in ("GET", "BINGET", "LONG_BINGET"):
                    pending.append(memo.get(arg))
                else:
                    if n in ("GLOBAL", "INST"):
                        module, _, name = str(arg).partition(" ")
                        found.append((n, f"{module}.{name}", _import_risk(module, name) or ""))
                    elif n == "STACK_GLOBAL":
                        if len(pending) >= 2 and pending[-1] and pending[-2]:
                            module, name = pending[-2], pending[-1]
                            found.append((n, f"{module}.{name}", _import_risk(module, name) or ""))
                        else:
                            found.append((n, "unresolved", "medium"))
                    pending = []
            finished += 1
        except Exception as exc:
            if finished:  # raw tensor bytes follow the pickles in legacy torch files
                break
            if not opcodes:
                raise _NotPickle()
            found.append(("malformed", f"stream stops after {opcodes} opcodes: {exc}", "medium"))
            break
    if not opcodes:
        raise _NotPickle()
    return [f for f in found if f[2]]


def _scan_model(raw: bytes) -> Tuple[List[Dict[str, Any]], int]:
    """(findings, pickles scanned)."""
    rows: List[Dict[str, Any]] = []

    def add(file: str, data: bytes) -> bool:
        try:
            found = _pickle_findings(data)
        except _NotPickle:
            rows.append({"file": file, "finding": "not a readable pickle", "item": "", "severity": "medium"})
            return False
        for kind, item, severity in found:
            what = "dangerous import" if severity == "high" else "import outside the safe allowlist" if kind != "malformed" else "malformed pickle"
            rows.append({"file": file, "finding": f"{what} ({kind})", "item": _scrub(item), "severity": severity})
        return True

    if zipfile.is_zipfile(io.BytesIO(raw)):
        scanned = 0
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for info in zf.infolist():
                    if not info.filename.endswith(".pkl"):
                        continue
                    if info.file_size > MAX_MEMBER:
                        rows.append({"file": info.filename, "finding": "member too large to scan", "item": "", "severity": "medium"})
                        continue
                    with zf.open(info) as member:
                        data = member.read(MAX_MEMBER + 1)
                    if len(data) > MAX_MEMBER:
                        rows.append({"file": info.filename, "finding": "member too large to scan", "item": "", "severity": "medium"})
                    else:
                        scanned += add(info.filename, data)
        except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as exc:
            raise EngineError(f"The model file is a damaged or encrypted zip archive: {exc}")
        return rows, scanned
    if not add("model", raw):
        raise EngineError("The model file is neither a pickle nor a zip archive holding .pkl members, so it cannot be scanned. Pickle-based formats (.pkl, .pt, .pth, .bin) are supported")
    return rows, 1


PIN_NPM = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
PIN_PIP = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*===?\s*([^\s,;*]+)\s*(?:;.*)?$")


def _scan_manifest(text: str) -> Tuple[List[Dict[str, Any]], int]:
    """(findings, dependencies read)."""
    rows: List[Dict[str, Any]] = []
    total = 0
    if text.lstrip().startswith("{"):
        try:
            doc = json.loads(text)
        except ValueError as exc:
            raise EngineError(f"The dependency manifest is not valid JSON: {exc}")
        for section in ("dependencies", "devDependencies", "optionalDependencies"):
            deps = doc.get(section) if isinstance(doc, dict) else None
            if not isinstance(deps, dict):
                continue
            for name, version in deps.items():
                total += 1
                if not PIN_NPM.match(str(version).strip()):
                    rows.append({"file": "package.json", "finding": f"not pinned to an exact version ({section})", "item": f"{name}@{_scrub(str(version), 60)}", "severity": "medium"})
        return rows, total
    for line in text.splitlines():
        line = re.split(r"\s+#|\s+--", line.strip())[0].rstrip("\\").strip()
        if not line or line.startswith(("#", "-")):
            continue
        total += 1
        if not PIN_PIP.match(line):
            name = re.split(r"[\s<>=!~;@\[]", line, 1)[0]
            rows.append({"file": "requirements", "finding": "not pinned to an exact version", "item": name if "://" in line else _scrub(line, 80), "severity": "medium"})
    return rows, total


def model_scan(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    model, manifest = files.get("model"), files.get("manifest")
    if not model and not manifest:
        raise EngineError("Upload a model file, a dependency manifest, or both")
    rows: List[Dict[str, Any]] = []
    pickles = deps = 0
    if model:
        found, pickles = _scan_model(model)
        rows += found
    if manifest:
        found, deps = _scan_manifest(read_text(manifest, "The dependency manifest"))
        rows += found
    dangerous = sum(1 for r in rows if r["severity"] == "high")
    metrics = {"picklesScanned": pickles, "dependencies": deps, "findings": len(rows), "dangerousImports": dangerous,
               "unpinnedDependencies": sum(1 for r in rows if r["file"] in ("package.json", "requirements"))}
    if not pickles and not deps and not rows:
        return result("insufficient", "Nothing to scan: the model archive holds no .pkl members and the manifest lists no dependencies.", metrics)
    if not rows:
        return result("passed", f"No unsafe imports in {pickles} pickles and all {deps} dependencies are pinned.", metrics)
    return result("failed", f"{len(rows)} findings: {dangerous} dangerous imports and {len(rows) - dangerous} others across {pickles} pickles and {deps} dependencies.", metrics, rows)


# --- EV-SEC-17 tool poisoning --------------------------------------------------------------------

MAX_DESCRIPTION = 1500
STEERING = re.compile(r"(?i)\b(?:instead|before|after|always|first|must|never|rather than|prior to|override|replace|do not use|don't use|whenever)\b")


def _descriptions(node: Any, path: str):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "description" and isinstance(value, str):
                yield f"{path}.description", value
            else:
                yield from _descriptions(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _descriptions(value, f"{path}[{i}]")


def tool_poisoning(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    doc = read_json(files["tools"], "The tool manifest")
    tools = doc.get("tools") if isinstance(doc, dict) else doc
    if not isinstance(tools, list) or not tools:
        raise EngineError('The tool manifest must be an MCP tools/list result {"tools": [...]} or a non-empty list of tools')
    for t in tools:
        if not isinstance(t, dict) or not t.get("name"):
            raise EngineError("Every tool needs a name")
    names = [str(t["name"]) for t in tools]
    rows = []
    for tool in tools:
        name = str(tool["name"])
        fields = [("description", tool["description"])] if isinstance(tool.get("description"), str) else []
        fields += list(_descriptions(tool.get("inputSchema"), "inputSchema"))
        for field, text in fields:
            cats, snippet = [], ""
            for cat, hit in scan(text, INSTRUCTIONS):
                if cat not in cats:
                    cats.append(cat)
                    snippet = snippet or hit
            cross = [n for n in names if n != name and re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text)]
            if cross and STEERING.search(text):
                cats.append("cross_tool_reference")
                snippet = snippet or ", ".join(cross[:3])
            if len(text) > MAX_DESCRIPTION:
                cats.append("oversized_description")
                snippet = snippet or text
            if cats:
                rows.append({"tool": name, "field": field, "categories": cats,
                             "snippet": _scrub(snippet).encode("ascii", "backslashreplace").decode()})
    flagged = len({r["tool"] for r in rows})
    metrics = {"tools": len(tools), "flaggedTools": flagged, "findings": len(rows)}
    if not rows:
        return result("passed", f"None of the {len(tools)} tools carries hidden instructions, cross-tool steering or an oversized description.", metrics)
    return result("failed", f"{flagged} of {len(tools)} tools look poisoned: {', '.join(sorted({r['tool'] for r in rows})[:6])}.", metrics, rows)


# --- EV-AGT-01 tool least privilege --------------------------------------------------------------

def _norm(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def least_privilege(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    perms = read_csv(files["permissions"], "The permissions file")
    log = read_csv(files["calls"], "The tool-call log")
    columns(perms, ["tool", "permission", "risk"], "The permissions file")
    columns(log, ["tool"], "The tool-call log")
    risk = _norm(perms["risk"]).str.lower()
    bad = sorted(set(risk) - {"low", "medium", "high"})
    if bad:
        raise EngineError(f"risk must be low, medium or high; the permissions file has {', '.join(repr(b) for b in bad[:5])}")
    log_tool = _norm(log["tool"])
    if "permission" in log.columns:
        log_perm = _norm(log["permission"])
        pairs = Counter(zip(log_tool, log_perm))
        blank = Counter(t for t, p in zip(log_tool, log_perm) if not p)  # a call that names no permission counts for the tool's grants
    else:
        tools = Counter(log_tool)
    rows = []
    for tool, perm in zip(_norm(perms["tool"])[risk == "high"], _norm(perms["permission"])[risk == "high"]):
        calls = pairs[(tool, perm)] + (blank[tool] if perm else 0) if "permission" in log.columns else tools[tool]
        rows.append({"tool": tool, "permission": perm, "risk": "high", "calls": int(calls), "unused": calls == 0})
    rows.sort(key=lambda r: not r["unused"])
    unused = sum(1 for r in rows if r["unused"])
    metrics = {"grants": len(perms), "highRiskGrants": len(rows), "unusedHighRisk": unused, "loggedCalls": len(log)}
    if not rows:
        return result("passed", f"No high-risk grants among {len(perms)} permissions.", metrics)
    if unused:
        return result("failed", f"{unused} of {len(rows)} high-risk grants were never used in {len(log)} logged calls; revoke them.", metrics, rows)
    return result("passed", f"All {len(rows)} high-risk grants were used in the {len(log)} logged calls.", metrics, rows)


# --- EV-AGT-03 MCP server permission audit -------------------------------------------------------

SHELLS = {"sh", "bash", "zsh", "dash", "fish", "cmd", "powershell", "pwsh"}


def _broad_command(spec: Any) -> Optional[Tuple[str, str]]:
    if not isinstance(spec, dict):
        return None
    command = re.sub(r"\.(?:exe|cmd|bat)$", "", str(spec.get("command") or "").replace("\\", "/").rsplit("/", 1)[-1].lower())
    args = [str(a) for a in spec.get("args") or []] if isinstance(spec.get("args"), list) else []
    if command in SHELLS:
        return "launched through a shell", command
    if command == "npx" and any(a in ("-y", "--yes") for a in args):
        package = next((a for a in args if not a.startswith("-")), "")
        body = package[1:] if package.startswith("@") else package
        version = body.split("@", 1)[1] if "@" in body else ""
        if not re.match(r"\d+\.\d+\.\d+", version):
            return "npx -y without a pinned version", "(url)" if "://" in package else re.sub(r"(?<=.)@[^@/]*$", "", package) or "npx"
    return None


def mcp_audit(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    config = read_json(files["config"], "The MCP config")
    servers = (config.get("mcpServers") or config.get("servers")) if isinstance(config, dict) else None
    if not isinstance(servers, dict) or not servers:
        raise EngineError('The MCP config must hold servers under "mcpServers" (or "servers"), as {"name": {...}}')
    register = read_csv(files["register"], "The register")
    columns(register, ["server", "tool"], "The register")
    reg_server, reg_tool = _norm(register["server"]), _norm(register["tool"])
    whole = set(reg_server[reg_tool == "*"])
    known = set(reg_server)
    tools_ok = set(zip(reg_server, reg_tool))
    inventory = None
    if files.get("inventory"):
        inventory = read_json(files["inventory"], "The tool inventory")
        if not isinstance(inventory, dict) or not all(isinstance(v, list) for v in inventory.values()):
            raise EngineError('The tool inventory must be {"server": ["tool", ...]}')
    rows = []
    for server, spec in servers.items():
        if server not in known:
            rows.append({"kind": "unapproved server", "server": server, "tool": "", "detail": "not in the register"})
        broad = _broad_command(spec)
        if broad:
            rows.append({"kind": "broad command", "server": server, "tool": "", "detail": f"{broad[0]}: {broad[1]}"})
    unapproved_servers = sum(1 for r in rows if r["kind"] == "unapproved server")
    for server, tools in (inventory or {}).items():
        if server in known and server not in whole:
            rows += [{"kind": "unapproved tool", "server": server, "tool": str(t), "detail": "not in the register"}
                     for t in tools if (server, str(t)) not in tools_ok]
    unapproved_tools = sum(1 for r in rows if r["kind"] == "unapproved tool")
    broad_count = sum(1 for r in rows if r["kind"] == "broad command")
    metrics = {"servers": len(servers), "unapprovedServers": unapproved_servers, "unapprovedTools": unapproved_tools,
               "broadCommands": broad_count, "toolLevelChecked": inventory is not None}
    note = f" {broad_count} servers launch through a broad command (reported, not counted)." if broad_count else ""
    scope = "" if inventory is not None else " Tool-level checks need a tool inventory."
    if unapproved_servers or unapproved_tools:
        return result("failed", f"{unapproved_servers} unapproved servers and {unapproved_tools} unapproved tools among {len(servers)} configured servers.{note}", metrics, rows)
    return result("passed", f"All {len(servers)} configured servers are in the register.{scope}{note}", metrics, rows)


# --- EV-AGT-04 browser-agent domain allowlist ----------------------------------------------------

def _host(url: str) -> Tuple[str, str]:
    """(hostname, url without credentials, query or fragment); blank host when unparseable."""
    try:
        parts = urlsplit(url if "://" in url else "//" + url)
        host = (parts.hostname or "").rstrip(".").lower()
    except ValueError:
        return "", url[:SNIPPET]
    return host, f"{parts.scheme + ':' if parts.scheme else ''}//{host}{parts.path}"


def domain_allowlist(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    log = read_csv(files["navigation"], "The navigation log")
    columns(log, ["url"], "The navigation log")
    exact, wild = set(), set()
    for line in read_text(files["allowlist"], "The allowlist").splitlines():
        entry = line.split("#", 1)[0].strip().lower()
        if "://" in entry:
            entry = _host(entry)[0]
        if entry.startswith("*."):
            wild.add(entry[2:])
        elif entry:
            exact.add(entry)
    if not exact and not wild:
        raise EngineError("The allowlist has no domains; list one per line, such as example.com or *.example.com")
    offenders: Counter = Counter()
    hosts: Dict[str, str] = {}
    visits = 0
    for raw in _norm(log["url"]):
        visits += 1
        host, shown = _host(raw)
        if host and (host in exact or any(host.endswith("." + w) for w in wild)):
            continue
        offenders[shown or "(blank)"] += 1
        hosts[shown or "(blank)"] = host or "(unparseable)"
    off = sum(offenders.values())
    rows = [{"url": u, "host": hosts[u], "count": n} for u, n in offenders.most_common()]
    metrics = {"navigations": visits, "offAllowlist": off, "onAllowlist": visits - off, "distinctOffAllowlistUrls": len(rows)}
    if off:
        return result("failed", f"{off} of {visits} navigations went off the allowlist, to {len({r['host'] for r in rows})} hosts; first {rows[0]['host']}.", metrics, rows)
    return result("passed", f"All {visits} navigations stayed on the allowlist.", metrics)


# --- EV-MON-03 cost and token thresholds ---------------------------------------------------------

ALERT_AT = 0.8


def cost_budget(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    frame = read_csv(files["usage"], "The usage file")
    amount_col = str(params.get("amount_column") or "cost").strip()
    columns(frame, [amount_col], "The usage file")
    if params.get("budget") in (None, ""):
        raise EngineError("budget is required")
    budget = number(params, "budget", 0.0)
    if budget <= 0:
        raise EngineError("budget must be greater than zero")
    period = str(params.get("period") or "").strip().lower()
    date_col = str(params.get("date_column") or "").strip()
    if period not in ("", "month"):
        raise EngineError("period must be blank or month")
    if period == "month" and not date_col:
        raise EngineError("period month needs date_column")
    amounts = pd.to_numeric(frame[amount_col], errors="coerce")
    unreadable = int(amounts.isna().sum())
    if unreadable == len(frame):
        raise EngineError(f"No value in column {amount_col} is a number")
    if period == "month":
        columns(frame, [date_col], "The usage file")
        dates = pd.to_datetime(frame[date_col], errors="coerce", utc=True)
        if dates.isna().any():
            raise EngineError(f"Row {int(dates.isna().to_numpy().argmax()) + 1} of {date_col} is not a date")
        spend = amounts.groupby(dates.dt.strftime("%Y-%m")).sum()
    else:
        spend = pd.Series({"total": amounts.sum()})
    rows = []
    for name, value in spend.items():
        share = float(value) / budget
        rows.append({"period": str(name), "spend": round(float(value), 4), "budget": budget, "share": round(share, 4),
                     "state": "over" if share > 1 else "alert" if share >= ALERT_AT else "ok"})
    over = [r for r in rows if r["state"] == "over"]
    top = max(rows, key=lambda r: r["share"])
    metrics = {"spend": round(float(amounts.sum()), 4), "budget": budget, "periods": len(rows), "overBudgetPeriods": len(over),
               "peakShare": top["share"], "alert": top["share"] >= ALERT_AT, "unreadableAmounts": unreadable}
    skipped = f" {unreadable} rows had no readable amount and were not counted." if unreadable else ""
    if over:
        where = f" in {len(over)} of {len(rows)} periods ({', '.join(r['period'] for r in over[:4])})" if period else ""
        return result("failed", f"Spend exceeded the budget of {budget:,.2f}{where}; the peak was {top['spend']:,.2f} ({top['share']:.0%}).{skipped}", metrics, rows)
    if metrics["alert"]:
        return result("passed", f"Within budget, but spend has reached {top['share']:.0%} of {budget:,.2f}, past the 80% alert threshold.{skipped}", metrics, rows)
    return result("passed", f"Spend is within budget: peak {top['spend']:,.2f} of {budget:,.2f} ({top['share']:.0%}).{skipped}", metrics, rows)


# --- EV-MON-04 log completeness ------------------------------------------------------------------

def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, (list, dict)) and not value)


def log_completeness(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    required = split(params.get("required_fields"))
    if not required:
        raise EngineError("required_fields is required; list the field names every record must carry, comma-separated")
    text = read_text(files["log"], "The run log")
    records: List[Tuple[int, Dict[str, Any]]] = []
    if text.lstrip().startswith("{"):
        for no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError as exc:
                raise EngineError(f"Line {no} of the run log is not valid JSON: {exc}")
            if not isinstance(rec, dict):
                raise EngineError(f"Line {no} of the run log is not a JSON object")
            records.append((no, rec))
    else:
        try:
            records = [(no, row) for no, row in enumerate(csv.DictReader(io.StringIO(text)), 1)]
        except csv.Error as exc:
            raise EngineError(f"The run log is not readable CSV: {exc}")
    if not records:
        raise EngineError("The run log has no records")
    absent = [f for f in required if not any(f in rec for _, rec in records)]
    if absent:
        raise EngineError(f"No record has the field {', '.join(absent)}; check the spelling against the log")
    rows, missing_by = [], Counter()
    for no, rec in records:
        gone = [f for f in required if _empty(rec.get(f))]
        missing_by.update(gone)
        if gone:
            rows.append({"record": no, "missing": ", ".join(gone)})
    complete = len(records) - len(rows)
    metrics = {"records": len(records), "complete": complete, "incomplete": len(rows), "completeness": round(complete / len(records), 4),
               "missingByField": dict(missing_by), "requiredFields": required}
    if rows:
        return result("failed", f"{complete} of {len(records)} records are complete ({_pct(complete, len(records))}); most often missing: {missing_by.most_common(1)[0][0]}.", metrics, rows)
    return result("passed", f"All {len(records)} records carry every required field.", metrics)


# --- EV-MON-05 agent loop and runaway detection --------------------------------------------------

def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in ("1", "1.0", "true", "yes", "y")


def runaway(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    frame = read_csv(files["calls"], "The tool-call log")
    columns(frame, ["run_id", "tool"], "The tool-call log")
    max_repeats, max_calls = int(number(params, "max_repeats", 5)), int(number(params, "max_calls", 200))
    if max_repeats < 1 or max_calls < 1:
        raise EngineError("max_repeats and max_calls must be at least 1")
    if "timestamp" in frame.columns:
        ts = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        if ts.isna().any():
            raise EngineError(f"Row {int(ts.isna().to_numpy().argmax()) + 1} of timestamp is not a date")
        frame = frame.assign(_ts=ts).sort_values("_ts", kind="stable").reset_index(drop=True)
    has_alert = "alerted" in frame.columns
    runs = _norm(frame["run_id"]).replace("", "(no run_id)").tolist()
    tools = _norm(frame["tool"]).tolist()
    args = _norm(frame["args"]).tolist() if "args" in frame.columns else [""] * len(frame)
    alerts = [_truthy(v) for v in frame["alerted"]] if has_alert else [False] * len(frame)
    stats: Dict[str, Dict[str, Any]] = {}
    last: Dict[str, Tuple[str, str]] = {}
    streak: Dict[str, int] = {}
    for run, tool, arg, alert in zip(runs, tools, args, alerts):
        s = stats.setdefault(run, {"calls": 0, "longest": 0, "tool": "", "alerted": False})
        s["calls"] += 1
        s["alerted"] = s["alerted"] or alert
        streak[run] = streak[run] + 1 if last.get(run) == (tool, arg) else 1
        last[run] = (tool, arg)
        if streak[run] > s["longest"]:
            s["longest"], s["tool"] = streak[run], tool
    rows = []
    for run, s in stats.items():
        reasons = []
        if s["longest"] > max_repeats:
            reasons.append(f"{s['longest']} identical consecutive calls to {s['tool']} (limit {max_repeats})")
        if s["calls"] > max_calls:
            reasons.append(f"{s['calls']} calls in the run (limit {max_calls})")
        if reasons:
            rows.append({"run_id": run, "reason": "; ".join(reasons), "calls": s["calls"], "longestRepeat": s["longest"],
                         "alerted": s["alerted"] if has_alert else None, "undetected": not (has_alert and s["alerted"])})
    rows.sort(key=lambda r: not r["undetected"])
    undetected = sum(1 for r in rows if r["undetected"])
    metrics = {"runs": len(stats), "calls": len(frame), "runawayEpisodes": len(rows), "undetected": undetected, "alertColumn": has_alert}
    if not rows:
        return result("passed", f"No runaway episodes in {len(stats)} runs ({len(frame)} calls).", metrics)
    why = "the log has no alerted column, so none counts as detected" if not has_alert else "no alerted=1 appears in them"
    if undetected:
        return result("failed", f"{len(rows)} runaway episodes in {len(stats)} runs; {undetected} undetected ({why if undetected == len(rows) else 'no alerted=1 in those runs'}).", metrics, rows)
    return result("passed", f"{len(rows)} runaway episodes in {len(stats)} runs, and every one raised an alert.", metrics, rows)


# --- EV-PRV-03 processing location ---------------------------------------------------------------

def processing_location(files: Dict[str, bytes], params: Dict[str, Any]) -> Dict[str, Any]:
    frame = read_csv(files["provider_log"], "The provider log")
    col = str(params.get("region_column") or "region").strip()
    columns(frame, [col], "The provider log")
    approved = {r.lower() for r in split(params.get("approved"))}
    if not approved:
        raise EngineError("approved is required; list the regions calls may be processed in, comma-separated")
    regions = _norm(frame[col])
    rows = []
    for region, n in regions.value_counts().items():
        ok = region.lower() in approved
        rows.append({"region": region or "(blank)", "calls": int(n), "approved": ok})
    rows.sort(key=lambda r: (r["approved"], -r["calls"]))
    inside = sum(r["calls"] for r in rows if r["approved"])
    metrics = {"calls": len(frame), "approvedCalls": inside, "outsideCalls": len(frame) - inside,
               "approvedShare": round(inside / len(frame), 4), "regions": len(rows)}
    if inside == len(frame):
        return result("passed", f"All {len(frame)} calls were processed in approved regions.", metrics, rows)
    out = [r for r in rows if not r["approved"]]
    return result("failed", f"{len(frame) - inside} of {len(frame)} calls ({_pct(len(frame) - inside, len(frame))}) were processed outside approved regions, in {', '.join(r['region'] for r in out[:5])}.", metrics, rows)


ENGINES: List[Engine] = [
    Engine(
        id="EV-DEV-01",
        method="Case-insensitive regex families look for a role definition, a scope limit and override resistance in the prompt, plus any clauses you add; every clause must match.",
        slots=(Slot("system_prompt", "System prompt", "The full system prompt as plain text.", "text"),),
        params=(Param("extra_clauses", "Extra clauses", 'Optional JSON list of {"name": ..., "pattern": ...} regexes the prompt must also match.', "json"),),
        run=system_prompt,
    ),
    Engine(
        id="EV-DEV-02",
        method="Each line of the file is matched against known credential formats and password-style assignments; any hit fails and is shown masked.",
        slots=(Slot("file", "Prompt or configuration file", "A prompt, .env, YAML or JSON file as text.", "text"),),
        run=file_secrets,
    ),
    Engine(
        id="EV-SEC-16",
        method="Each line of the context or log export is matched against credential formats; personal-data hits are counted separately and do not fail the check.",
        slots=(Slot("context", "Context or log export", "An agent or tool context dump, or a log, as text.", "text"),),
        run=context_secrets,
    ),
    Engine(
        id="EV-SEC-14",
        method=(
            "Pickle opcodes are walked without loading the file and any import outside a safe allowlist is flagged; "
            "dependencies that are not pinned to an exact version are flagged."
        ),
        slots=(
            Slot("model", "Model file", "A pickle, or a zip such as a PyTorch .pt, holding .pkl members.", "binary", False),
            Slot("manifest", "Dependency manifest", "requirements.txt or package.json.", "text", False),
        ),
        run=model_scan,
    ),
    Engine(
        id="EV-SEC-17",
        method=(
            "Every tool and schema property description is checked for hidden instructions, steering that names another tool, "
            f"and length over {MAX_DESCRIPTION} characters."
        ),
        slots=(Slot("tools", "Tool manifest", 'An MCP tools/list result {"tools": [...]} or a bare list of tools.', "json"),),
        run=tool_poisoning,
    ),
    Engine(
        id="EV-AGT-01",
        method="Each high-risk permission is matched to the logged calls that use it; one with no call is unused and fails.",
        slots=(
            Slot("permissions", "Permissions", "CSV with columns tool, permission and risk (low, medium or high)."),
            Slot("calls", "Tool-call log", "CSV with column tool and, optionally, permission."),
        ),
        run=least_privilege,
    ),
    Engine(
        id="EV-AGT-03",
        method="Each configured MCP server, and each tool when an inventory is given, is looked up in the approved register; broad launch commands are reported.",
        slots=(
            Slot("config", "MCP config", 'JSON with servers under "mcpServers" or "servers".', "json"),
            Slot("register", "Approved register", 'CSV with columns server and tool; tool "*" approves the whole server.'),
            Slot("inventory", "Tool inventory", 'Optional JSON {"server": ["tool", ...]} for tool-level checks.', "json", False),
        ),
        run=mcp_audit,
    ),
    Engine(
        id="EV-AGT-04",
        method="The host of every navigated URL is compared with the allowlist; *.example.com covers subdomains only.",
        slots=(
            Slot("navigation", "Navigation log", "CSV with column url."),
            Slot("allowlist", "Allowlist", "One domain per line; *.example.com covers subdomains.", "text"),
        ),
        run=domain_allowlist,
    ),
    Engine(
        id="EV-MON-03",
        method="Spend in the amount column is summed, per month when asked, and compared with the budget; 80% of it raises an alert.",
        slots=(Slot("usage", "Usage log", "CSV with one row per call or day and an amount column."),),
        params=(
            Param("amount_column", "Amount column", "Column holding cost or tokens.", "text", "cost"),
            Param("budget", "Budget", "The limit for the total, or for each period.", "number", None, True),
            Param("date_column", "Date column", "Column holding the date; used with period."),
            Param("period", "Period", "month checks each month against the budget; blank checks the total."),
        ),
        run=cost_budget,
    ),
    Engine(
        id="EV-MON-04",
        method="A record is complete when every required field is present and non-empty; the share of complete records must be 100%.",
        slots=(Slot("log", "Run log", "CSV, or JSON Lines with one record per line.", "csv"),),
        params=(Param("required_fields", "Required fields", "Field names every record must carry, comma-separated.", "text", None, True),),
        run=log_completeness,
    ),
    Engine(
        id="EV-MON-05",
        method=(
            "Per run, the longest streak of identical consecutive calls and the call count are checked against the limits; "
            "a run over either limit with no alerted=1 is an undetected runaway."
        ),
        slots=(Slot("calls", "Tool-call log", "CSV with run_id and tool; optional args, timestamp and alerted (0 or 1)."),),
        params=(
            Param("max_repeats", "Max repeats", "Identical consecutive calls allowed in a run.", "number", 5),
            Param("max_calls", "Max calls", "Calls allowed in a run.", "number", 200),
        ),
        run=runaway,
    ),
    Engine(
        id="EV-PRV-03",
        method="The region of every call is compared with the approved list; all calls must be inside it.",
        slots=(Slot("provider_log", "Provider log", "CSV with one row per call and a region column."),),
        params=(
            Param("region_column", "Region column", "Column holding the processing region.", "text", "region"),
            Param("approved", "Approved regions", "Regions calls may be processed in, comma-separated.", "text", None, True),
        ),
        run=processing_location,
    ),
]
