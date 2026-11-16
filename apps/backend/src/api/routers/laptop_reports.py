"""
The FairMind laptop script: a read-only check the organisation's device management runs once a day on each
laptop. It reports AI apps, editor extensions, MCP server names and, per app, whether it is signed in with a
work or personal account. The script compares the account's domain on the laptop; only the answer leaves it.
It also lists edge AI models that local runtimes downloaded (Ollama, LM Studio, the Hugging Face cache), by name.
It never reads prompts, files, tokens or MCP server settings, and it sends only what matches the catalogue.

GET  /shadow-ai/laptop-script              whether it is set up, its company domains, how many laptops reported
PUT  /shadow-ai/laptop-script              set the company domains (creates the source on first use)
POST /shadow-ai/laptop-script/token        a new ingest token, shown once; the old one stops working
GET  /shadow-ai/laptop-script/download     the script for macos or windows, with the domains and address filled in
POST /public/laptop-report                 a laptop's report, with the ingest token as a bearer token
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import integrations as hub
from api.routes.ai_governance import _caller_org
from api.routes.discovery_sources.catalog import _BY_KEY as SERVICES_BY_KEY
from api.routes.discovery_sources.catalog import APPS, EXTENSIONS, by_extension_id, by_installed
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

router = APIRouter(prefix="/shadow-ai/laptop-script", tags=["shadow-ai"], dependencies=[Depends(org_member)])
public_router = APIRouter(tags=["shadow-ai"])

KIND = "laptop_script"
SCRIPT_VERSION = "1"
_DOMAIN = re.compile(r"^(?=.{3,253}$)[a-z0-9-]+(\.[a-z0-9-]+)+$")
ACCOUNT_APPS = ("cursor", "claude")  # apps whose signed-in account the script can read without a token


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def domains_of(value: Any) -> List[str]:
    """Company email domains from free text: comma or space separated, lower case, each a plain domain."""
    out = []
    if isinstance(value, (list, tuple)):
        value = " ".join(str(v) for v in value)
    for d in re.split(r"[\s,;]+", str(value or "").lower()):
        d = d.strip().lstrip("@").rstrip(".")
        if d and _DOMAIN.match(d) and d not in out:
            out.append(d)
    return out


def _row(db: Session, org: str) -> Optional[Any]:
    return db.execute(
        text(f"SELECT {hub._INTEGRATION_COLS} FROM governance_integrations WHERE org_id = :org AND kind = :k ORDER BY created_at LIMIT 1"), {"org": org, "k": KIND}
    ).fetchone()


# ---------------------------------------------------------------------------
# A laptop's report
# ---------------------------------------------------------------------------


class ReportApp(BaseModel):
    name: str = Field(max_length=200)
    bundle_id: Optional[str] = Field(default=None, max_length=200)
    version: Optional[str] = Field(default=None, max_length=64)


class ReportExtension(BaseModel):
    id: str = Field(max_length=200)
    editor: Optional[str] = Field(default=None, max_length=40)


class ReportMcp(BaseModel):
    name: str = Field(max_length=120)
    client: str = Field(max_length=40)
    command: Optional[str] = Field(default=None, max_length=120)  # the program's name only, never its arguments


class ReportModel(BaseModel):
    runtime: Literal["ollama", "lm_studio", "huggingface"]
    name: str = Field(max_length=200)
    size: Optional[int] = Field(default=None, ge=0)


class ReportAccount(BaseModel):
    app: str = Field(max_length=40)
    domain: Literal["work", "personal"]


class LaptopReport(BaseModel):
    serial: Optional[str] = Field(default=None, max_length=64)
    name: Optional[str] = Field(default=None, max_length=120)
    user: Optional[str] = Field(default=None, max_length=200)
    os: Optional[str] = Field(default=None, max_length=40)
    apps: List[ReportApp] = Field(default_factory=list, max_length=200)
    extensions: List[ReportExtension] = Field(default_factory=list, max_length=200)
    mcp_servers: List[ReportMcp] = Field(default_factory=list, max_length=200)
    accounts: List[ReportAccount] = Field(default_factory=list, max_length=20)
    models: List[ReportModel] = Field(default_factory=list, max_length=300)
    script_version: Optional[str] = Field(default=None, max_length=20)


def device_record(r: LaptopReport) -> Dict[str, Any]:
    """The report as a laptop record Shadow AI merges with other sources; anything outside the catalogue is dropped."""
    apps: List[Dict[str, Any]] = []
    for a in r.apps:
        s = by_installed(a.name, a.bundle_id)
        if s and all(x["service"] != s.key or x["kind"] != "installed" for x in apps):
            apps.append({"service": s.key, "name": a.name, "version": a.version, "kind": "installed"})
    for e in r.extensions:
        s = by_extension_id(e.id)
        if s and all(x["service"] != s.key or x["kind"] != "extension" for x in apps):
            apps.append({"service": s.key, "name": e.id, "version": None, "kind": "extension"})
    accounts = {a.app: a.domain for a in r.accounts if a.app in ACCOUNT_APPS and a.app in SERVICES_BY_KEY}
    mcp = {(m.name.strip(), m.client.strip()): m.command for m in r.mcp_servers if m.name.strip()}
    user = (r.user or "").strip().lower() or None
    return {
        "serial": (r.serial or "").strip() or None,
        "name": (r.name or "").strip() or None,
        "device_id": None,
        "user": user,
        "apps": apps,
        "accounts": [{"service": k, "class": v} for k, v in sorted(accounts.items())],
        "mcp": [{"name": n, "client": c, "command": (cmd or "").split("/")[-1].split("\\")[-1][:120] or None} for (n, c), cmd in sorted(mcp.items())],
        "os": r.os,
        "models": [{"runtime": m.runtime, "name": m.name.strip(), "size": m.size or 0} for m in r.models if m.name.strip()],
    }


@public_router.post("/laptop-report")
def receive_report(body: LaptopReport, http: Request, db: Session = Depends(get_db)):
    auth = http.headers.get("authorization") or ""
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if len(token) < 20:
        raise HTTPException(status_code=401, detail="Send the ingest token as a bearer token")
    hub._ensure_tables()
    digest = _hash(token)
    row = db.execute(
        text("SELECT id, org_id FROM governance_integrations WHERE kind = :k AND config_json LIKE :h"), {"k": KIND, "h": f'%"ingest_token_hash": "{digest}"%'}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="This ingest token is not valid; create a new one in Shadow AI")
    record = device_record(body)
    key = record["serial"] or f"{(record['name'] or '').lower()}|{record['user'] or ''}"
    if key == "|":
        raise HTTPException(status_code=422, detail="The report names no serial number and no laptop")
    now = _now()
    db.execute(text("DELETE FROM governance_laptop_reports WHERE integration_id = :i AND device_key = :k"), {"i": row[0], "k": key})
    db.execute(
        text("INSERT INTO governance_laptop_reports (id, org_id, integration_id, device_key, report_json, received_at) VALUES (:id, :org, :i, :k, :r, :now)"),
        {"id": str(uuid.uuid4()), "org": row[1], "i": row[0], "k": key, "r": json.dumps(record), "now": now},
    )
    db.execute(text("UPDATE governance_integrations SET last_synced_at = :now WHERE id = :i"), {"now": now, "i": row[0]})
    db.commit()
    return {"received": True, "apps": len(record["apps"]), "accounts": len(record["accounts"]), "mcpServers": len(record["mcp"])}


def reports_as_facts(db: Session, org: str, max_age_days: int = 30) -> List[tuple]:
    """Every laptop's latest report as one facts row, as the other laptop sources store theirs."""
    rows = db.execute(text("SELECT report_json, received_at FROM governance_laptop_reports WHERE org_id = :org"), {"org": org}).fetchall()
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    devices = [json.loads(r[0]) for r in rows if datetime.fromisoformat(r[1]).timestamp() >= cutoff]
    return [(KIND, json.dumps({"devices": devices}))] if devices else []


# ---------------------------------------------------------------------------
# Setting it up
# ---------------------------------------------------------------------------


class ScriptSetup(BaseModel):
    domains: str = Field(min_length=1, max_length=2000)


@router.get("")
def script_status(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    org = _caller_org(http)
    row = _row(db, org)
    if not row:
        return {"connected": False, "domains": [], "hasToken": False, "laptops": 0, "lastReportAt": None}
    config = hub._load_json_value(row[4], {})
    n, last = db.execute(text("SELECT COUNT(*), MAX(received_at) FROM governance_laptop_reports WHERE integration_id = :i"), {"i": row[0]}).fetchone()
    return {"connected": True, "integrationId": row[0], "domains": domains_of(config.get("domains")), "hasToken": bool(config.get("ingest_token_hash")), "laptops": n, "lastReportAt": last}


@router.put("")
def set_domains(body: ScriptSetup, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    domains = domains_of(body.domains)
    if not domains:
        raise HTTPException(status_code=422, detail="Give at least one company email domain, such as acme.com")
    row = _row(db, org)
    if row:
        config = {**hub._load_json_value(row[4], {}), "domains": domains}
        db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": row[0]})
    else:
        db.execute(
            text("INSERT INTO governance_integrations (id, org_id, kind, name, config_json, created_at) VALUES (:id, :org, :k, :n, :c, :now)"),
            {"id": str(uuid.uuid4()), "org": org, "k": KIND, "n": "Laptop script", "c": json.dumps({"domains": domains}), "now": _now()},
        )
    db.commit()
    return script_status(http, db)


@router.post("/token")
def new_token(http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    row = _row(db, org)
    if not row:
        raise HTTPException(status_code=409, detail="Set your company domains first")
    token = "fmls_" + secrets.token_urlsafe(32)
    config = {**hub._load_json_value(row[4], {}), "ingest_token_hash": _hash(token)}
    db.execute(text("UPDATE governance_integrations SET config_json = :c WHERE id = :id"), {"c": json.dumps(config), "id": row[0]})
    db.commit()
    return {"token": token}


def script_config(domains: List[str], url: str) -> Dict[str, Any]:
    names = sorted({n for names, _ in APPS.values() for n in names})
    bundles = sorted({b for _, bundles in APPS.values() for b in bundles})
    return {"url": url, "domains": domains, "names": names, "bundles": bundles, "extensions": sorted(EXTENSIONS), "version": SCRIPT_VERSION}


@router.get("/download")
def download(os: Literal["macos", "windows"], http: Request, db: Session = Depends(get_db)):
    from config.settings import settings

    hub._ensure_tables()
    row = _row(db, _caller_org(http))
    if not row:
        raise HTTPException(status_code=409, detail="Set your company domains first")
    domains = domains_of(hub._load_json_value(row[4], {}).get("domains"))
    url = f"{settings.frontend_url.rstrip('/')}/api/proxy/api/v1/public/laptop-report"
    config = json.dumps(script_config(domains, url), separators=(",", ":"))
    body = (MACOS if os == "macos" else WINDOWS).replace("__CONFIG__", config)
    name = "fairmind-laptop-check.sh" if os == "macos" else "fairmind-laptop-check.ps1"
    return {"filename": name, "script": body}


# ---------------------------------------------------------------------------
# The scripts. Values come from the catalogue and validated domains only.
# ---------------------------------------------------------------------------

MACOS = r"""#!/bin/zsh
# FairMind laptop check. Read-only; run by your device management as root, once a day.
# Reports AI apps, editor extensions, MCP server names and, per app, whether it is signed in with a
# work or personal account. The account's domain is compared here; the address never leaves the laptop.
# It never reads prompts, files, tokens or MCP server settings.
# Usage: fairmind-laptop-check.sh <ingest token>    (Jamf: put the token in script parameter 4)
TOKEN="${4:-$1}"
[ -z "$TOKEN" ] && { echo "Pass the FairMind ingest token"; exit 1; }
/usr/bin/osascript -l JavaScript - "$TOKEN" <<'JXA'
ObjC.import('Foundation')
const CONFIG = __CONFIG__
const app = Application.currentApplication(); app.includeStandardAdditions = true
function sh(cmd) { try { return app.doShellScript(cmd) } catch (e) { return '' } }
function q(s) { return "'" + String(s).replace(/'/g, "'\\''") + "'" }
function read(p) { const s = $.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null); return s.isNil() ? null : ObjC.unwrap(s) }
function json(p) { const t = read(p); if (!t) return null; try { return JSON.parse(t) } catch (e) { return null } }
function ls(d) { const a = $.NSFileManager.defaultManager.contentsOfDirectoryAtPathError(d, null); return a.isNil() ? [] : ObjC.deepUnwrap(a) }
function norm(n) { let p = null; n = String(n || '').trim().toLowerCase(); while (n !== p) { p = n; n = n.replace(/\.(app|exe)$/, '').replace(/\s*\((user|machine|x64|x86|arm64)\)$/, '').replace(/\s+(version\s+)?v?\d+(\.\d+)*$/, '').trim() } return n }
function domainOf(email) { const m = /^[^@\s]+@([^@\s]+)$/.exec(String(email || '').trim().toLowerCase()); if (!m) return null; return CONFIG.domains.some(d => m[1] === d || m[1].endsWith('.' + d)) ? 'work' : 'personal' }
function run(argv) {
  const token = argv[0]
  const user = sh('stat -f%Su /dev/console')
  const home = user && user !== 'root' ? sh('dscl . -read /Users/' + q(user) + ' NFSHomeDirectory | awk \'{print $2}\'') : ''
  const report = { serial: sh("ioreg -rd1 -c IOPlatformExpertDevice | awk -F'\"' '/IOPlatformSerialNumber/{print $4}'"), name: sh('scutil --get ComputerName'), user: user, os: 'macOS ' + sh('sw_vers -productVersion'), apps: [], extensions: [], mcp_servers: [], accounts: [], script_version: CONFIG.version }
  for (const dir of ['/Applications', home + '/Applications']) {
    for (const f of ls(dir)) {
      if (!f.endsWith('.app')) continue
      const plist = dir + '/' + f + '/Contents/Info'
      const bundle = sh('defaults read ' + q(plist) + ' CFBundleIdentifier')
      if (!CONFIG.names.includes(norm(f)) && !CONFIG.bundles.includes(bundle.toLowerCase())) continue
      report.apps.push({ name: f.replace(/\.app$/, ''), bundle_id: bundle, version: sh('defaults read ' + q(plist) + ' CFBundleShortVersionString') })
    }
  }
  for (const [editor, dir] of [['VS Code', home + '/.vscode/extensions'], ['Cursor', home + '/.cursor/extensions'], ['Windsurf', home + '/.windsurf/extensions']]) {
    for (const f of ls(dir)) { const id = f.toLowerCase().replace(/-\d+(\.\d+)*(-[a-z0-9-]+)?$/, ''); if (CONFIG.extensions.includes(id)) report.extensions.push({ id: id, editor: editor }) }
  }
  const lib = home + '/Library/Application Support'
  const cc = json(home + '/.claude.json') || {}
  const mcpFiles = [['Claude Desktop', json(lib + '/Claude/claude_desktop_config.json'), 'mcpServers'], ['Cursor', json(home + '/.cursor/mcp.json'), 'mcpServers'], ['Claude Code', cc, 'mcpServers'], ['Windsurf', json(home + '/.codeium/windsurf/mcp_config.json'), 'mcpServers'], ['VS Code', json(lib + '/Code/User/mcp.json'), 'servers']]
  for (const p of Object.values(cc.projects || {})) mcpFiles.push(['Claude Code', p, 'mcpServers'])
  for (const [client, doc, key] of mcpFiles) {
    for (const [name, s] of Object.entries((doc && doc[key]) || {})) {
      const cmd = s && (s.command ? String(s.command).split('/').pop() : (s.url || s.serverUrl) ? 'remote' : null)
      report.mcp_servers.push({ name: String(name).slice(0, 120), client: client, command: cmd })
    }
  }
  report.models = []
  for (const host of ls(home + '/.ollama/models/manifests')) for (const ns of ls(home + '/.ollama/models/manifests/' + host)) for (const model of ls(home + '/.ollama/models/manifests/' + host + '/' + ns)) for (const tag of ls(home + '/.ollama/models/manifests/' + host + '/' + ns + '/' + model)) report.models.push({ runtime: 'ollama', name: (ns === 'library' ? model : ns + '/' + model) + ':' + tag })
  for (const root of [home + '/.lmstudio/models', home + '/.cache/lm-studio/models']) for (const pub of ls(root)) for (const model of ls(root + '/' + pub)) report.models.push({ runtime: 'lm_studio', name: pub + '/' + model })
  for (const d of ls(home + '/.cache/huggingface/hub')) if (d.startsWith('models--')) report.models.push({ runtime: 'huggingface', name: d.slice(8).replace('--', '/') })
  report.models = report.models.slice(0, 300)
  const db = lib + '/Cursor/User/globalStorage/state.vscdb'
  // Only the cached email is selected; the same table holds sign-in tokens, which are never read.
  const cursorEmail = sh('/usr/bin/sqlite3 -readonly ' + q('file:' + db + '?immutable=1') + " \"SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'\"").replace(/^"|"$/g, '')
  const claudeEmail = (cc.oauthAccount || {}).emailAddress
  for (const [svc, email] of [['cursor', cursorEmail], ['claude', claudeEmail]]) {
    const d = domainOf(email)
    if (d) report.accounts.push({ app: svc, domain: d })
    if (d === 'work' && !report.user.includes('@')) report.user = String(email).toLowerCase()  // a company address names the person
  }
  const tmp = sh('mktemp -d')
  const body = $.NSString.alloc.initWithUTF8String(JSON.stringify(report)); body.writeToFileAtomicallyEncodingError(tmp + '/r.json', true, $.NSUTF8StringEncoding, null)
  const hdr = $.NSString.alloc.initWithUTF8String('Authorization: Bearer ' + token); hdr.writeToFileAtomicallyEncodingError(tmp + '/h', true, $.NSUTF8StringEncoding, null)
  sh('chmod 600 ' + q(tmp + '/h'))
  const out = sh('curl -sS -m 30 -X POST -H "Content-Type: application/json" -H @' + q(tmp + '/h') + ' --data-binary @' + q(tmp + '/r.json') + ' ' + q(CONFIG.url))
  sh('rm -rf ' + q(tmp))
  return out
}
JXA
"""

WINDOWS = r"""# FairMind laptop check. Read-only; run by your device management as SYSTEM, once a day.
# Reports AI apps, editor extensions, MCP server names and, per app, whether it is signed in with a
# work or personal account. The account's domain is compared here; the address never leaves the laptop.
# It never reads prompts, files, tokens or MCP server settings.
# Usage: powershell -ExecutionPolicy Bypass -File fairmind-laptop-check.ps1 -Token <ingest token>
param([string]$Token = $env:FAIRMIND_TOKEN)
if (-not $Token) { Write-Error 'Pass the FairMind ingest token'; exit 1 }
$Config = ConvertFrom-Json @'
__CONFIG__
'@
function Norm([string]$n) { $p = $null; $n = "$n".Trim().ToLower(); while ($n -ne $p) { $p = $n; $n = ($n -replace '\.(app|exe)$', '' -replace '\s*\((user|machine|x64|x86|arm64)\)$', '' -replace '\s+(version\s+)?v?\d+(\.\d+)*$', '').Trim() }; $n }
function DomainOf([string]$email) { if ("$email" -notmatch '^[^@\s]+@([^@\s]+)$') { return $null }; $d = $Matches[1].ToLower(); foreach ($c in $Config.domains) { if ($d -eq $c -or $d.EndsWith(".$c")) { return 'work' } }; 'personal' }
function ReadJson([string]$p) { if (Test-Path -LiteralPath $p) { try { Get-Content -LiteralPath $p -Raw | ConvertFrom-Json } catch { $null } } }
$account = (Get-CimInstance Win32_ComputerSystem).UserName
$local = if ($account) { $account.Split('\')[-1] } else { '' }
$homeDir = if ($local) { Join-Path $env:SystemDrive "Users\$local" } else { '' }
$report = [ordered]@{ serial = (Get-CimInstance Win32_BIOS).SerialNumber; name = $env:COMPUTERNAME; user = $local; os = 'Windows ' + [Environment]::OSVersion.Version.ToString(); apps = @(); extensions = @(); mcp_servers = @(); accounts = @(); script_version = $Config.version }
$keys = @('HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*', 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
if ($account) { try { $sid = (New-Object System.Security.Principal.NTAccount($account)).Translate([System.Security.Principal.SecurityIdentifier]).Value; $keys += "Registry::HKEY_USERS\$sid\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" } catch {} }
$seen = @{}
foreach ($k in $keys) { foreach ($a in (Get-ItemProperty -Path $k -ErrorAction SilentlyContinue)) { $n = Norm $a.DisplayName; if ($n -and $Config.names -contains $n -and -not $seen[$n]) { $seen[$n] = $true; $report.apps += @{ name = $a.DisplayName; version = $a.DisplayVersion } } } }
foreach ($pair in @(@('VS Code', "$homeDir\.vscode\extensions"), @('Cursor', "$homeDir\.cursor\extensions"), @('Windsurf', "$homeDir\.windsurf\extensions"))) {
  if (Test-Path -LiteralPath $pair[1]) { foreach ($d in Get-ChildItem -LiteralPath $pair[1] -Directory) { $id = $d.Name.ToLower() -replace '-\d+(\.\d+)*(-[a-z0-9-]+)?$', ''; if ($Config.extensions -contains $id) { $report.extensions += @{ id = $id; editor = $pair[0] } } } }
}
$cc = ReadJson "$homeDir\.claude.json"
$files = @(@('Claude Desktop', (ReadJson "$homeDir\AppData\Roaming\Claude\claude_desktop_config.json"), 'mcpServers'), @('Cursor', (ReadJson "$homeDir\.cursor\mcp.json"), 'mcpServers'), @('Claude Code', $cc, 'mcpServers'), @('Windsurf', (ReadJson "$homeDir\.codeium\windsurf\mcp_config.json"), 'mcpServers'), @('VS Code', (ReadJson "$homeDir\AppData\Roaming\Code\User\mcp.json"), 'servers'))
if ($cc -and $cc.projects) { foreach ($p in $cc.projects.PSObject.Properties) { $files += ,@('Claude Code', $p.Value, 'mcpServers') } }
foreach ($f in $files) { $doc = $f[1]; if ($doc -and $doc.($f[2])) { foreach ($s in $doc.($f[2]).PSObject.Properties) { $cmd = if ($s.Value.command) { Split-Path -Leaf "$($s.Value.command)" } elseif ($s.Value.url -or $s.Value.serverUrl) { 'remote' } else { $null }; $report.mcp_servers += @{ name = "$($s.Name)"; client = $f[0]; command = $cmd } } } }
$models = @()
$om = "$homeDir\.ollama\models\manifests"
if (Test-Path -LiteralPath $om) { foreach ($t in Get-ChildItem -LiteralPath $om -Recurse -File -Depth 3) { $rel = $t.FullName.Substring($om.Length + 1).Split('\'); if ($rel.Count -eq 4) { $n = if ($rel[1] -eq 'library') { $rel[2] } else { "$($rel[1])/$($rel[2])" }; $models += @{ runtime = 'ollama'; name = "$($n):$($rel[3])" } } } }
foreach ($root in @("$homeDir\.lmstudio\models", "$homeDir\.cache\lm-studio\models")) { if (Test-Path -LiteralPath $root) { foreach ($p in Get-ChildItem -LiteralPath $root -Directory) { foreach ($m in Get-ChildItem -LiteralPath $p.FullName -Directory) { $models += @{ runtime = 'lm_studio'; name = "$($p.Name)/$($m.Name)" } } } } }
$hf = "$homeDir\.cache\huggingface\hub"
if (Test-Path -LiteralPath $hf) { foreach ($d in Get-ChildItem -LiteralPath $hf -Directory -Filter 'models--*') { $models += @{ runtime = 'huggingface'; name = ($d.Name.Substring(8) -replace '--', '/') } } }
$report.models = @($models | Select-Object -First 300)
# Cursor keeps its account in a SQLite file that Windows cannot read without extra tools, so only Claude Code is checked here.
if ($cc -and $cc.oauthAccount) { $d = DomainOf $cc.oauthAccount.emailAddress; if ($d) { $report.accounts += @{ app = 'claude'; domain = $d }; if ($d -eq 'work') { $report.user = "$($cc.oauthAccount.emailAddress)".ToLower() } } }
Invoke-RestMethod -Uri $Config.url -Method Post -Headers @{ Authorization = "Bearer $Token" } -ContentType 'application/json' -Body ($report | ConvertTo-Json -Depth 6 -Compress)
"""
