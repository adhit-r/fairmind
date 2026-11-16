"""
Shadow AI: AI used outside what the organisation approved, worked out by comparing what the
connected sources already read. No source here reads prompts, replies or file contents.

GET  /shadow-ai                     findings (open, expected, resolved), stories, the approved-versus-used map, coverage
GET  /shadow-ai/laptops             laptops with AI on them, merged across sources (search with q)
GET  /shadow-ai/evidence            every AI tool for one person or laptop: on the laptop, traffic, company seat, stance
GET  /shadow-ai/tools               every known AI service with the organisation's stance on it
PUT  /shadow-ai/tools/{service}     set or clear the stance on one service
POST /shadow-ai/findings/expected   mark a finding as expected, with a reason
POST /shadow-ai/findings/reopen     undo that
POST /shadow-ai/findings/nudge      email the person a finding is about

Checks, each from sources that already exist:
- personal account: traffic to an approved tool whose company accounts sign in through Okta,
  by someone with no Okta sign-in to it in 30 days (proxy logs + Okta); or use of a tool, seen in
  traffic or installed on the person's laptop, by someone with no company seat (seat list + proxy
  logs or a device inventory). Traffic plus no seat is confirmed.
- leaver's seat: a company seat still held by someone who has left (seat list + Okta or Entra)
- leaver's key: a vendor or gateway key owned by someone who has left (OpenAI or LiteLLM + Okta or Entra)
- skips the gateway: direct calls to a model API while a LiteLLM gateway is in use (proxy logs + LiteLLM)
- not allowed: any sighting of a service the organisation does not allow, installs included
- self-consent: people consented to an unapproved AI app without an admin (Entra)
- MCP server not in the registry: an MCP config in code naming a server the registry lacks (GitHub + MCP registry)
"""

from __future__ import annotations

import json
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import integrations as hub
from api.routes.ai_governance import _caller_org
from api.routes.discovery_sources.catalog import SERVICES
from api.routes.org_scope import org_member, org_mutator
from database.connection import get_db

router = APIRouter(prefix="/shadow-ai", tags=["shadow-ai"], dependencies=[Depends(org_member)])

_BY_KEY = {s.key: s for s in SERVICES}
_BY_LABEL = {re.sub(r"[^a-z0-9]", "", s.label.lower()): s for s in SERVICES}
_IP = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$|^[0-9a-f:]+:[0-9a-f:]*$", re.I)
_SEVERITY = {"critical": 0, "high": 1, "medium": 2}
MAP_COLUMNS = 8
NO_TEAM = "No team"


def _norm(v: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(v or "").lower())


def _when(v: Any) -> Optional[datetime]:
    """An epoch number or ISO string as an aware datetime."""
    if v is None or v == "":
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _day(d: Optional[datetime]) -> str:
    return d.strftime("%-d %b %Y") if d else "an unknown date"


def _service_of(a: Dict[str, Any]):
    ext = str(a["externalId"])
    if ext.startswith("service:"):
        return _BY_KEY.get(ext.split(":", 1)[1])
    if a["metadata"].get("service"):
        return _BY_LABEL.get(_norm(a["metadata"]["service"]))
    return None


class People:
    """Directory facts merged from every sign-in source: team and whether the person has left."""

    def __init__(self, rows: List[Any]):
        self.by_email: Dict[str, Dict[str, Any]] = {}
        for source, facts_json in rows:
            facts = json.loads(facts_json or "{}")
            left = set(facts.get("left_statuses") or [])
            for email, p in (facts.get("people") or {}).items():
                self.by_email[email] = {**p, "source": source, "left": p.get("status") in left}
        self.by_local: Dict[str, List[str]] = defaultdict(list)
        for email in self.by_email:
            self.by_local[email.split("@")[0]].append(email)

    def resolve(self, who: str) -> Optional[str]:
        """The email a log's user field names: itself, or the one directory email with that name before the @."""
        w = (who or "").strip().lower()
        if "\\" in w:
            w = w.split("\\")[-1]  # DOMAIN\\user
        if "@" in w:
            return w
        hits = self.by_local.get(w) or []
        return hits[0] if len(hits) == 1 else None

    def team(self, email: Optional[str]) -> str:
        return (self.by_email.get(email or "") or {}).get("team") or NO_TEAM


def _laptop_keys(d: Dict[str, Any]) -> List[str]:
    keys = [f"s:{d['serial'].strip().upper()}"] if d.get("serial") else []
    keys += [f"d:{d['device_id'].strip().lower()}"] if d.get("device_id") else []
    if not keys and d.get("name") and d.get("user"):
        keys = [f"n:{_norm(d['name'])}|{d['user']}"]
    if not keys and d.get("name"):
        keys = [f"o:{d['source']}:{_norm(d['name'])}"]  # one source's own name for it; never joins another source
    return keys


def merge_laptops(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One record per laptop from every device source. Serial number and Microsoft device ID are strong keys;
    a record with neither merges on name plus person. A name alone never merges."""
    parent = list(range(len(raw)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    first: Dict[str, int] = {}
    for i, d in enumerate(raw):
        for k in _laptop_keys(d):
            if k in first:
                parent[find(i)] = find(first[k])
            else:
                first[k] = i
    groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for i, d in enumerate(raw):
        groups[find(i)].append(d)
    out = []
    for members in groups.values():
        names = sorted({m["name"] for m in members if m.get("name")})
        serial = next((m["serial"].strip().upper() for m in members if m.get("serial")), None)
        apps: Dict[str, Dict[str, Any]] = {}
        for m in members:
            for a in m.get("apps") or []:
                e = apps.setdefault(a["service"], {"versions": set(), "sources": set(), "kinds": set()})
                if a.get("version"):
                    e["versions"].add(a["version"])
                e["sources"].add(m["source"])
                e["kinds"].add(a.get("kind") or "installed")
        out.append(
            {
                "id": min(k for m in members for k in _laptop_keys(m)) if any(_laptop_keys(m) for m in members) else f"x:{len(out)}",
                "keys": sorted({k for m in members for k in _laptop_keys(m)}),
                "name": names[0] if names else serial or "Unnamed laptop",
                "names": names,
                "serial": serial,
                "users": sorted({m["user"] for m in members if m.get("user")}),
                "sources": sorted({m["source"] for m in members}),
                "apps": {k: {"versions": sorted(v["versions"]), "sources": sorted(v["sources"]), "kinds": sorted(v["kinds"])} for k, v in apps.items()},
            }
        )
    out.sort(key=lambda l: l["name"])
    return out


class Fleet:
    """Seat lists and laptops from every seat and device source."""

    def __init__(self, rows: List[Any]):
        self.seats: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self.complete: Dict[str, bool] = {}
        raw: List[Dict[str, Any]] = []
        traffic: List[Dict[str, Any]] = []
        for source, facts_json in rows:
            facts = json.loads(facts_json or "{}")
            for svc, held in (facts.get("seats") or {}).items():
                for email, v in held.items():
                    self.seats[svc][email] = {**v, "source": source}
                # Two lists for one tool (two Cursor teams) are compared only if both carry emails.
                self.complete[svc] = self.complete.get(svc, True) and bool((facts.get("complete") or {}).get(svc))
            raw += [{**d, "source": source} for d in facts.get("devices") or []]
            traffic += [{**t, "source": source} for t in facts.get("traffic") or []]
        self.laptops = merge_laptops(raw)
        by_key = {k: lt for lt in self.laptops for k in lt["keys"]}
        # From the laptop script: which account each AI app is signed in with, and MCP servers in app settings.
        self.accounts: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)  # service -> person -> class, laptops
        self.mcp: Dict[str, Dict[str, Any]] = {}  # server name -> laptops, clients, commands
        for d in raw:
            lt = next((by_key[k] for k in _laptop_keys(d) if k in by_key), None)
            where = lt["name"] if lt else d.get("name") or "a laptop"
            for acc in d.get("accounts") or []:
                if d.get("user"):
                    e = self.accounts[acc["service"]].setdefault(d["user"].lower(), {"class": acc["class"], "laptops": set()})
                    e["class"] = "personal" if "personal" in (e["class"], acc["class"]) else e["class"]
                    e["laptops"].add(where)
            for m in d.get("mcp") or []:
                e = self.mcp.setdefault(m["name"], {"laptops": set(), "clients": set(), "commands": set()})
                e["laptops"].add(where)
                e["clients"].add(m["client"])
                if m.get("command"):
                    e["commands"].add(m["command"])
        # service -> person as the source names them -> requests, laptops, sources
        self.traffic: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        for t in traffic:
            if not t.get("user"):
                continue
            lt = next((by_key[k] for k in _laptop_keys({**t, "user": None}) if k in by_key), None)
            e = self.traffic[t["service"]].setdefault(t["user"].lower(), {"requests": 0, "laptops": set(), "sources": set()})
            e["requests"] += int(t.get("requests") or 0)
            e["sources"].add(t["source"])
            if lt or t.get("name"):
                e["laptops"].add(lt["name"] if lt else t["name"])
        self.installs: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        for lt in self.laptops:
            for u in lt["users"]:
                for svc in lt["apps"]:
                    self.installs[u][svc].append(lt)
        self._local = {svc: {e.split("@")[0] for e in held} for svc, held in self.seats.items()}

    def compared(self, svc: str) -> bool:
        """Whether a seat list for the service can be compared with who uses it."""
        return bool(self.seats.get(svc)) and self.complete.get(svc, False)

    def holds(self, svc: str, email: str) -> bool:
        """A seat for this person; the name before the @ also counts, since a sign-in name and a seat email can differ in domain."""
        return email in self.seats.get(svc, {}) or email.split("@")[0] in self._local.get(svc, set())


def _laptops_detail(laptops: List[Dict[str, Any]], svc: str) -> str:
    names = [lt["name"] for lt in laptops]
    sources = sorted({hub_label(x) for lt in laptops for x in lt["apps"][svc]["sources"]})
    shown = ", ".join(names[:3]) + (f" and {len(names) - 3} more" if len(names) > 3 else "")
    return f"Installed on {shown}, seen by {', '.join(sources)}"


def _laptop_traffic(s: Any, t: Dict[str, Any]) -> Dict[str, str]:
    where = sorted(t["laptops"])
    shown = ", ".join(where[:3]) + (f" and {len(where) - 3} more" if len(where) > 3 else "")
    n = t["requests"]
    return {
        "source": "devices", "title": "Laptop traffic",
        "detail": f"{n} connection{'s' if n != 1 else ''} to {s.label}" + (f" from {shown}" if shown else "") + f", seen by {', '.join(sorted(hub_label(x) for x in t['sources']))}",
    }


_RANK = {"possible": 0, "likely": 1, "confirmed": 2}
LAPTOP_SOURCES = ("jamf", "intune", "defender", "crowdstrike", "chrome", "fleet", "laptop_script")


def _finding(key: str, kind: str, title: str, severity: str, confidence: str, subject: str, evidence: List[Dict[str, str]], verdict: str, **extra: Any) -> Dict[str, Any]:
    return {"key": key, "type": kind, "title": title, "severity": severity, "confidence": confidence, "subject": subject, "evidence": evidence, "verdict": verdict, **extra}


def detect(assets: List[Dict[str, Any]], people: People, stance: Dict[str, Dict[str, Any]], now: datetime, fleet: Optional[Fleet] = None) -> List[Dict[str, Any]]:
    """Every current finding. Pure: the inputs are what the sources stored and the organisation's stance."""
    out: List[Dict[str, Any]] = []
    fleet = fleet or Fleet([])
    proxy = [a for a in assets if a["source"] == "proxy_logs"]
    okta_by_service: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in assets:
        s = _service_of(a)
        if a["source"] == "okta" and s:
            okta_by_service[s.key].append(a)

    # Personal accounts. One candidate per tool and person, whichever checks raise it; the strongest certainty wins.
    cands: Dict[tuple, Dict[str, Any]] = {}

    work = {(svc, people.resolve(who) or who) for svc, by_who in fleet.accounts.items() for who, a in by_who.items() if a["class"] == "work"}

    def candidate(svc: str, who: str, email: Optional[str], conf: str, evidence: List[Dict[str, str]]) -> None:
        if conf != "confirmed" and (svc, email or who.lower()) in work:
            return  # the laptop shows this app signed in with a company account
        c = cands.setdefault((svc, email or who.lower()), {"who": who, "email": email, "conf": conf, "evidence": []})
        if _RANK[conf] > _RANK[c["conf"]]:
            c["conf"] = conf
        titles = {e["title"] for e in c["evidence"]}
        c["evidence"] += [e for e in evidence if e["title"] not in titles]

    def traffic(a: Dict[str, Any], s: Any, who: str, n: int) -> Dict[str, str]:
        return {"source": "proxy_logs", "title": "Proxy logs", "detail": f"{n} request{'s' if n != 1 else ''} to {', '.join(a['metadata'].get('hosts') or [s.label])} by {who}"}

    # Traffic to an approved tool whose company accounts sign in through Okta, with no Okta sign-in.
    for a in proxy:
        s = _service_of(a)
        st = stance.get(s.key) if s else None
        if not s or not st or st["status"] not in ("approved", "limited") or not st["sso_required"] or not okta_by_service.get(s.key):
            continue
        sso = {u.lower() for o in okta_by_service[s.key] for u in (o["metadata"].get("sso_users") or [])}
        capped = any(o["metadata"].get("sso_sign_ins_capped") for o in okta_by_service[s.key])
        for who, n in sorted((a["metadata"].get("requests_by_user") or {}).items()):
            if _IP.match(who.strip()):
                continue  # an address, not a person
            email = people.resolve(who)
            if email in sso or who.lower() in sso or (email and fleet.compared(s.key) and fleet.holds(s.key, email)):
                continue
            candidate(
                s.key, who, email, "possible" if capped else "likely",
                [traffic(a, s, who, n), {"source": "okta", "title": "Okta", "detail": f"No sign-in to the company {s.label} app for this person in 30 days. Company accounts sign in through Okta."}],
            )

    # Use of a tool by someone with no company seat: traffic confirms it, an install alone makes it likely.
    for svc in [k for k in fleet.seats if fleet.compared(k) and (stance.get(k) or {}).get("status") != "not_allowed"]:
        s = _BY_KEY.get(svc)
        if not s:
            continue
        seat_source = hub_label(next(iter(fleet.seats[svc].values()))["source"])
        no_seat = {"source": "seats", "title": seat_source, "detail": f"No company {s.label} seat for this person"}
        for a in proxy:
            if _service_of(a) is not s:
                continue
            for who, n in sorted((a["metadata"].get("requests_by_user") or {}).items()):
                email = None if _IP.match(who.strip()) else people.resolve(who)
                if email and not fleet.holds(svc, email):
                    candidate(svc, who, email, "confirmed", [traffic(a, s, who, n), no_seat])
        for who, t in sorted(fleet.traffic.get(svc, {}).items()):
            email = people.resolve(who)
            if email and not fleet.holds(svc, email):
                candidate(svc, who, email, "confirmed", [_laptop_traffic(s, t), no_seat])
        for who, by_svc in fleet.installs.items():
            email = people.resolve(who)
            if svc in by_svc and email and not fleet.holds(svc, email):
                candidate(svc, who, email, "likely", [{"source": "devices", "title": "Laptops", "detail": _laptops_detail(by_svc[svc], svc)}, no_seat])

    # Signed in with an account outside the company's domains, as the laptop script reports.
    for svc, by_who in fleet.accounts.items():
        s = _BY_KEY.get(svc)
        if not s or (stance.get(svc) or {}).get("status") not in ("approved", "limited"):
            continue
        for who, a in sorted(by_who.items()):
            if a["class"] == "personal":
                where = ", ".join(sorted(a["laptops"])[:3])
                candidate(svc, who, people.resolve(who), "confirmed", [{"source": "devices", "title": "Signed in", "detail": f"{s.label} on {where} is signed in with an account outside your company domains, seen by the laptop script"}])

    for (svc, _), c in sorted(cands.items()):
        s = _BY_KEY[svc]
        if c["conf"] == "confirmed":
            verdict = f"A personal account: {s.label} is in use by someone with no company seat. Work sent there is outside your agreement with {s.vendor}."
            confirm = None
        else:
            verdict = f"Likely a personal account: {s.label} is in use, but not through your company account. Work sent there is outside your agreement with {s.vendor}."
            confirm = (
                f"Traffic from this person to {s.label} would confirm it." if fleet.compared(svc)
                else f"A {s.label} seat list, or a web gateway that reports the account's domain, would confirm it."
            )
        email = c["email"]
        out.append(
            _finding(
                f"personal:{svc}:{(email or c['who']).lower()}", "personal_account", f"Personal {s.label} account", "high", c["conf"], c["who"], c["evidence"], verdict,
                confirm=confirm, service=svc, person=email, team=people.team(email),
            )
        )

    # A company seat still held by someone who has left.
    for svc, held in fleet.seats.items():
        s = _BY_KEY.get(svc)
        for email, v in held.items():
            p = people.by_email.get(email)
            if not s or not p or not p["left"]:
                continue
            left_at, used = _when(p.get("status_changed")), _when(v.get("last_active"))
            where = hub_label(v["source"])
            evidence = [
                {"source": p["source"], "title": "Okta" if p["source"] == "okta" else "Entra ID", "detail": f"{email} left on {_day(left_at)}" if left_at else f"{email}'s account is turned off"},
                {"source": "seats", "title": where, "detail": f"Still holds a {s.label} seat" + (f", last used {_day(used)}" if used else "")},
            ]
            after = bool(used and left_at and used > left_at)
            out.append(
                _finding(
                    f"leaver_seat:{svc}:{email}", "leaver_seat", f"A leaver still holds a {s.label} seat", "critical" if after else "high", "confirmed", email, evidence,
                    (f"The seat was used after its owner left. Remove it in {where} now." if after else f"Remove the seat in {where}. It keeps access open and costs money."),
                    service=svc, person=email, team=people.team(email),
                )
            )

    # A leaver's key: OpenAI keys carry an owner email and when they were last used; LiteLLM keys an owner.
    for a in assets:
        if a["source"] not in ("openai", "litellm") or a["status"] == "ignored":
            continue
        email = (str(a["metadata"].get("owner") or "").strip().lower()) or None
        p = people.by_email.get(email or "")
        if not p or not p["left"]:
            continue
        left_at = _when(p.get("status_changed"))
        used = _when(a["metadata"].get("last_used_at"))
        where = "OpenAI" if a["source"] == "openai" else "LiteLLM gateway"
        gone = f"{email} left on {_day(left_at)}" if left_at else f"{email}'s account is turned off"
        evidence = [{"source": p["source"], "title": "Okta" if p["source"] == "okta" else "Entra ID", "detail": gone}]
        if used and left_at and used > left_at:
            sev, conf, verdict = "critical", "confirmed", f"The key was used after its owner left. Turn it off in {where}."
            evidence.append({"source": a["source"], "title": where, "detail": f"Key {a['name']} was last used {_day(used)}"})
        elif used and not left_at and used > now - timedelta(days=7):
            sev, conf, verdict = "critical", "likely", f"The key was used this week and its owner's account is turned off. Turn it off in {where}."
            evidence.append({"source": a["source"], "title": where, "detail": f"Key {a['name']} was last used {_day(used)}"})
        else:
            sev, conf, verdict = "high", "confirmed", f"The key still works though its owner has left. Turn it off in {where}, or give it a new owner."
            evidence.append({"source": a["source"], "title": where, "detail": f"Key {a['name']} is still active"})
        out.append(_finding(f"leaver:{a['id']}", "leaver_key", f"A leaver's {where} key is still active", sev, conf, a["name"], evidence, verdict, person=email, team=people.team(email)))

    # Calls straight to a model API while the organisation routes through a gateway.
    if any(a["source"] == "litellm" for a in assets):
        for a in proxy:
            s = _service_of(a)
            if not s or s.category != "api":
                continue
            clients = sorted(a["metadata"].get("users") or [])
            shown = ", ".join(clients[:3]) + (f" and {len(clients) - 3} more" if len(clients) > 3 else "")
            out.append(
                _finding(
                    f"bypass:{s.key}", "gateway_bypass", f"Calls to {s.label} that skip the gateway", "medium", "likely", s.label,
                    [
                        {"source": "proxy_logs", "title": "Proxy logs", "detail": f"{a['metadata'].get('requests', 0)} requests to {', '.join(a['metadata'].get('hosts') or [])}" + (f" from {shown}" if shown else "")},
                        {"source": "litellm", "title": "LiteLLM gateway", "detail": "Your model calls are meant to go through the gateway"},
                    ],
                    "These calls do not pass the gateway's keys, budgets and logs. If one of these clients is the gateway itself, mark it as expected.",
                    service=s.key,
                )
            )

    # Any sighting of a service the organisation does not allow.
    seen: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for a in assets:
        s = _service_of(a)
        if s and (stance.get(s.key) or {}).get("status") == "not_allowed":
            seen[s.key].append(a)
    installed: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for lt in fleet.laptops:
        for svc in lt["apps"]:
            if (stance.get(svc) or {}).get("status") == "not_allowed":
                installed[svc].append(lt)
    talked = {k for k in fleet.traffic if (stance.get(k) or {}).get("status") == "not_allowed"}
    for key in sorted(set(seen) | set(installed) | talked):
        s = _BY_KEY[key]
        evidence = [{"source": a["source"], "title": hub_label(a["source"]), "detail": _seen_detail(a)} for a in seen[key] if a["source"] not in LAPTOP_SOURCES]
        if installed[key]:
            evidence.append({"source": "devices", "title": "Laptops", "detail": _laptops_detail(installed[key], key)})
        for t in fleet.traffic.get(key, {}).values():
            evidence.append(_laptop_traffic(s, t))
            break  # one line is enough; the evidence grid lists every person
        out.append(_finding(f"not_allowed:{key}", "not_allowed", f"{s.label} is in use, and you do not allow it", "high", "confirmed", s.label, evidence, f"Ask the people using {s.label} to stop, and block it at your gateway.", service=key))

    # People consenting to an AI app on their own, for an app the organisation has not approved.
    for a in assets:
        s = _service_of(a)
        if a["source"] != "entra" or not a["metadata"].get("self_consent_only"):
            continue
        if s and (stance.get(s.key) or {}).get("status") in ("approved", "limited"):
            continue
        n = a["metadata"].get("users_who_consented") or 0
        out.append(
            _finding(
                f"consent:{a['externalId']}", "self_consent", f"People gave {a['name']} access on their own", "medium", "confirmed", a["name"],
                [{"source": "entra", "title": "Entra ID", "detail": f"{n} {'person' if n == 1 else 'people'} consented, and no admin did"}],
                "The app can read what those people granted it. Review it, then approve it or remove the consents.",
                service=s.key if s else None,
            )
        )

    # An MCP server in code that the organisation's registry does not list.
    registry = {_norm(a["metadata"].get("server_name", "").split("/")[-1]) for a in assets if a["source"] == "mcp_registry"} | {
        _norm(a["name"]) for a in assets if a["source"] == "mcp_registry"
    }
    if any(a["source"] == "mcp_registry" for a in assets):
        for a in assets:
            if a["source"] == "github" and a["kind"] == "mcp_server" and _norm(a["name"]) not in registry:
                out.append(
                    _finding(
                        f"mcp:{a['externalId']}", "unregistered_mcp", "MCP server not in your registry", "medium", "confirmed", a["name"],
                        [
                            {"source": "github", "title": "GitHub", "detail": f"{a['name']} is configured in {a['metadata'].get('repo')} ({a['metadata'].get('config_file') or 'MCP config'})"},
                            {"source": "mcp_registry", "title": "MCP registry", "detail": "Your registry has no server by that name"},
                        ],
                        "Agents in that repo can call a server nobody approved. Add it to the registry or remove it from the config.",
                    )
                )
        for name, m in sorted(fleet.mcp.items()):
            if _norm(name) in registry:
                continue
            where = sorted(m["laptops"])
            shown = ", ".join(where[:3]) + (f" and {len(where) - 3} more" if len(where) > 3 else "")
            how = f" ({', '.join(sorted(m['commands']))})" if m["commands"] else ""
            out.append(
                _finding(
                    f"mcp_laptop:{_norm(name)}", "unregistered_mcp", "MCP server on laptops, not in your registry", "medium", "confirmed", name,
                    [
                        {"source": "devices", "title": "Laptop script", "detail": f"{name}{how} is set up in {', '.join(sorted(m['clients']))} on {shown}"},
                        {"source": "mcp_registry", "title": "MCP registry", "detail": "Your registry has no server by that name"},
                    ],
                    "AI apps on these laptops can call a server nobody approved. Add it to the registry, or remove it from the app's settings.",
                    laptops=len(where),
                )
            )
    out.sort(key=lambda f: (_SEVERITY.get(f["severity"], 9), f["type"], f["key"]))
    return out


def _seen_detail(a: Dict[str, Any]) -> str:
    m = a["metadata"]
    if a["source"] == "proxy_logs":
        return f"{m.get('requests', 0)} requests" + (f" by {m.get('distinct_users')} people" if m.get("distinct_users") else "")
    if a["source"] == "okta":
        return f"{m.get('distinct_users_30_days', 0)} people signed in through Okta in 30 days"
    if a["source"] == "entra":
        return f"{m.get('users_who_consented', 0)} people consented"
    if "seats" in m:
        return f"{m['seats']} company seats, {m.get('active_30_days', 0)} used in 30 days"
    return a["name"]


def hub_label(kind: str) -> str:
    from api.routes.discovery_review import hub_source_label

    return hub_source_label(kind)


def usage_map(assets: List[Dict[str, Any]], people: People, stance: Dict[str, Dict[str, Any]], findings: List[Dict[str, Any]], fleet: Optional[Fleet] = None) -> Dict[str, Any]:
    """People per team and tool: company accounts, personal accounts, and use of tools that are not approved."""
    company: Dict[str, Set[str]] = defaultdict(set)
    users: Dict[str, Set[str]] = defaultdict(set)
    for a in assets:
        s = _service_of(a)
        if not s:
            continue
        if a["source"] == "okta":
            for u in a["metadata"].get("sso_users") or []:
                company[s.key].add(u.lower())
                users[s.key].add(u.lower())
        elif a["source"] == "proxy_logs":
            for u in a["metadata"].get("users") or []:
                if not _IP.match(u.strip()):
                    users[s.key].add(people.resolve(u) or u.lower())
    fleet = fleet or Fleet([])
    for who, by_svc in fleet.installs.items():
        for svc in by_svc:
            users[svc].add(people.resolve(who) or who)
    for svc, by_who in fleet.traffic.items():
        for who in by_who:
            users[svc].add(people.resolve(who) or who)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    for svc, held in fleet.seats.items():
        for email, v in held.items():
            used = _when(v.get("last_active"))
            if (used and used >= since) or email in users[svc]:
                company[svc].add(email)
                users[svc].add(email)
    personal: Dict[str, Set[str]] = defaultdict(set)
    for f in findings:
        if f["type"] == "personal_account" and f.get("status") != "expected":
            personal[f["service"]].add(f.get("person") or f["subject"].lower())
    keys = [k for k in stance if k in _BY_KEY]
    keys += sorted((k for k in users if k not in stance), key=lambda k: -len(users[k]))
    keys = keys[:MAP_COLUMNS]
    teams = sorted({people.team(u if "@" in u else None) for k in keys for u in users[k]} - {NO_TEAM})
    if any(people.team(u if "@" in u else None) == NO_TEAM for k in keys for u in users[k]):
        teams.append(NO_TEAM)
    cells: Dict[str, Dict[str, Dict[str, int]]] = {}
    for team in teams:
        row: Dict[str, Dict[str, int]] = {}
        for k in keys:
            in_team = lambda xs: {u for u in xs if people.team(u if "@" in u else None) == team}  # noqa: E731
            approved = (stance.get(k) or {}).get("status") in ("approved", "limited")
            row[k] = {
                "company": len(in_team(company[k])) if approved else 0,
                "personal": len(in_team(personal[k])) if approved else 0,
                "unapproved": 0 if approved else len(in_team(users[k])),
            }
        cells[team] = row
    tools = [{"key": k, "label": _BY_KEY[k].label, "status": (stance.get(k) or {}).get("status") or "not_reviewed", "teams": (stance.get(k) or {}).get("teams") or []} for k in keys]
    return {"tools": tools, "teams": teams, "cells": cells}


def _stance_of(stance: Dict[str, Dict[str, Any]], svc: str) -> str:
    return (stance.get(svc) or {}).get("status") or "not_reviewed"


def evidence(
    assets: List[Dict[str, Any]], people: People, fleet: Fleet, stance: Dict[str, Dict[str, Any]], person: Optional[str] = None, laptop: Optional[str] = None
) -> Dict[str, Any]:
    """Every AI tool for one person or one laptop, by kind of evidence: on the laptop, traffic, company seat, stance."""
    if laptop:
        laptops = [lt for lt in fleet.laptops if laptop == lt["id"] or laptop in lt["keys"]]
        whos = {u for lt in laptops for u in lt["users"]}
        persons = {people.resolve(u) or u for u in whos}
    else:
        p = (person or "").strip().lower()
        persons = {p}
        laptops = [lt for lt in fleet.laptops if any((people.resolve(u) or u) == p for u in lt["users"])]
    mine = lambda who: (people.resolve(who) or who.lower()) in persons  # noqa: E731
    rows: Dict[str, Dict[str, Any]] = {}

    def row(svc: str) -> Dict[str, Any]:
        s = _BY_KEY[svc]
        return rows.setdefault(svc, {"service": svc, "label": s.label, "vendor": s.vendor, "stance": _stance_of(stance, svc), "onLaptop": None, "traffic": None, "seat": None, "signedIn": None})

    for lt in laptops:
        for svc, a in lt["apps"].items():
            if svc not in _BY_KEY:
                continue
            on = row(svc)["onLaptop"] or {"laptops": [], "sources": set(), "kinds": set(), "versions": set()}
            on["laptops"].append(lt["name"])
            on["sources"] |= {hub_label(x) for x in a["sources"]}
            on["kinds"] |= set(a["kinds"])
            on["versions"] |= set(a["versions"])
            rows[svc]["onLaptop"] = on
    for svc, by_who in fleet.traffic.items():
        for who, t in by_who.items():
            if svc in _BY_KEY and mine(who):
                tr = row(svc)["traffic"] or {"requests": 0, "sources": set()}
                tr["requests"] += t["requests"]
                tr["sources"] |= {hub_label(x) for x in t["sources"]}
                rows[svc]["traffic"] = tr
    for svc, by_who in fleet.accounts.items():
        for who, a in by_who.items():
            if svc in _BY_KEY and mine(who):
                prev = row(svc)["signedIn"]
                cls = "personal" if a["class"] == "personal" or (prev and prev["class"] == "personal") else "work"
                rows[svc]["signedIn"] = {"class": cls, "laptops": sorted(set((prev or {}).get("laptops", [])) | a["laptops"])}
    for a in assets:
        s = _service_of(a)
        if a["source"] != "proxy_logs" or not s:
            continue
        n = sum(v for who, v in (a["metadata"].get("requests_by_user") or {}).items() if not _IP.match(who.strip()) and mine(who))
        if n:
            tr = row(s.key)["traffic"] or {"requests": 0, "sources": set()}
            tr["requests"] += n
            tr["sources"].add("Proxy logs")
            rows[s.key]["traffic"] = tr
    for svc in list(rows) + [k for k in fleet.seats if any(fleet.holds(k, x) for x in persons if "@" in x)]:
        if not fleet.seats.get(svc) or svc not in _BY_KEY:
            continue
        held = any(fleet.holds(svc, x) for x in persons if "@" in x)
        source = hub_label(next(iter(fleet.seats[svc].values()))["source"])
        row(svc)["seat"] = {"status": "held" if held else "none" if fleet.compared(svc) else "unknown", "source": source}
    out = []
    for r in rows.values():
        for k in ("onLaptop", "traffic"):
            if r[k]:
                r[k] = {kk: sorted(v) if isinstance(v, set) else v for kk, v in r[k].items()}
        out.append(r)
    out.sort(key=lambda r: (r["stance"] in ("approved", "limited"), r["label"]))
    subject = {"person": sorted(persons)[0] if not laptop and persons else None, "team": people.team(sorted(persons)[0]) if persons and not laptop else None}
    return {
        **subject,
        "laptops": [{"id": lt["id"], "name": lt["name"], "serial": lt["serial"], "sources": [hub_label(x) for x in lt["sources"]]} for lt in laptops],
        "people": sorted(persons),
        "rows": out,
    }


def laptop_list(people: People, fleet: Fleet, stance: Dict[str, Dict[str, Any]], q: str = "") -> List[Dict[str, Any]]:
    q = q.strip().lower()
    out = []
    for lt in fleet.laptops:
        users = [people.resolve(u) or u for u in lt["users"]]
        if q and not any(q in x.lower() for x in [*lt["names"], lt["serial"] or "", *users]):
            continue
        tools = [{"service": k, "label": _BY_KEY[k].label, "stance": _stance_of(stance, k)} for k in sorted(lt["apps"]) if k in _BY_KEY]
        out.append(
            {
                "id": lt["id"], "name": lt["name"], "serial": lt["serial"], "people": users, "team": people.team(users[0] if users else None),
                "sources": [hub_label(x) for x in lt["sources"]], "tools": tools,
                "flagged": sum(1 for t in tools if t["stance"] not in ("approved", "limited")),
            }
        )
    out.sort(key=lambda x: (-x["flagged"], x["name"].lower()))
    return out


STORY_MIN = 3
STORY_TYPES = ("personal_account", "not_allowed")


def stories(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Open findings about one tool in one team, when there are enough of them to be one story."""
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for f in findings:
        if f.get("status", "open") == "open" and f["type"] in STORY_TYPES and f.get("service") and f.get("team") and f["team"] != NO_TEAM:
            groups[(f["service"], f["team"])].append(f)
    out = []
    for (svc, team), fs in sorted(groups.items()):
        if len(fs) < STORY_MIN:
            continue
        s = _BY_KEY[svc]
        people = {f.get("person") or f["subject"] for f in fs}
        sure = sum(1 for f in fs if f["confidence"] == "confirmed")
        out.append(
            {
                "key": f"story:{svc}:{team}",
                "service": svc,
                "team": team,
                "title": f"{team} uses {s.label}",
                "summary": f"{len(people)} {'person' if len(people) == 1 else 'people'}, {len(fs)} findings, {sure} confirmed. Reviewing {s.label} once covers all of them.",
                "findingKeys": [f["key"] for f in fs],
            }
        )
    return out


# ---------------------------------------------------------------------------
# Loading and routes
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stance(db: Session, org: str) -> Dict[str, Dict[str, Any]]:
    rows = db.execute(
        text("SELECT service_key, status, teams_json, sso_required, note, updated_at, tenant_ids_json FROM governance_approved_ai_tools WHERE org_id = :org"), {"org": org}
    ).fetchall()
    return {
        r[0]: {"status": r[1], "teams": json.loads(r[2] or "[]"), "sso_required": bool(r[3]), "note": r[4], "updatedAt": r[5], "tenantIds": json.loads(r[6] or "[]")}
        for r in rows
    }


def _current(db: Session, org: str) -> Dict[str, Any]:
    hub._ensure_tables()
    assets = [hub._asset_out(r) for r in db.execute(text(f"SELECT {hub._ASSET_COLS} FROM governance_discovered_assets WHERE org_id = :org"), {"org": org}).fetchall()]
    from api.routes.laptop_reports import reports_as_facts

    facts = list(db.execute(text("SELECT source, facts_json FROM governance_source_facts WHERE org_id = :org"), {"org": org}).fetchall()) + reports_as_facts(db, org)
    people, fleet = People(facts), Fleet(facts)
    stance = _stance(db, org)
    kinds = {r[0] for r in db.execute(text("SELECT DISTINCT kind FROM governance_integrations WHERE org_id = :org"), {"org": org}).fetchall()}
    findings = detect(assets, people, stance, datetime.now(timezone.utc), fleet)
    return {"assets": assets, "people": people, "fleet": fleet, "stance": stance, "kinds": kinds, "findings": findings}


@router.get("")
def shadow_ai(http: Request, db: Session = Depends(get_db)):
    org = _caller_org(http)
    cur = _current(db, org)
    now = _now()
    states = {
        r[0]: {"status": r[1], "reason": r[2], "firstSeen": r[3], "lastSeen": r[4], "nudgedAt": r[5]}
        for r in db.execute(
            text("SELECT finding_key, status, reason, first_seen, last_seen, nudged_at FROM governance_shadow_states WHERE org_id = :org"), {"org": org}
        ).fetchall()
    }
    # ponytail: first and last seen are written on read; a scheduled sweep would date findings even when nobody opens the page.
    for f in cur["findings"]:
        st = states.get(f["key"])
        if st:
            db.execute(text("UPDATE governance_shadow_states SET last_seen = :now WHERE org_id = :org AND finding_key = :k"), {"now": now, "org": org, "k": f["key"]})
            st["lastSeen"] = now
        else:
            db.execute(
                text(
                    "INSERT INTO governance_shadow_states (id, org_id, finding_key, status, first_seen, last_seen, updated_at) "
                    "VALUES (:id, :org, :k, 'open', :now, :now, :now)"
                ),
                {"id": str(uuid.uuid4()), "org": org, "k": f["key"], "now": now},
            )
            st = states[f["key"]] = {"status": "open", "reason": None, "firstSeen": now, "lastSeen": now, "nudgedAt": None}
        f.update(st)
    db.commit()
    live = {f["key"] for f in cur["findings"]}
    resolved = [{"key": k, **v} for k, v in states.items() if k not in live and v["status"] == "open"]
    resolved.sort(key=lambda r: r["lastSeen"] or "", reverse=True)
    k = cur["kinds"]
    return {
        "findings": cur["findings"],
        "resolved": resolved[:100],
        "stories": stories(cur["findings"]),
        "map": usage_map(cur["assets"], cur["people"], cur["stance"], cur["findings"], cur["fleet"]),
        "coverage": {
            "proxyLogs": "proxy_logs" in k,
            "okta": "okta" in k,
            "entra": "entra" in k,
            "gateway": "litellm" in k,
            "mcpRegistry": "mcp_registry" in k,
            "people": len(cur["people"].by_email),
            "approvedTools": len(cur["stance"]),
            "ssoTools": sum(1 for s in cur["stance"].values() if s["sso_required"]),
            "seatLists": sorted(k for k in cur["fleet"].seats if cur["fleet"].compared(k)),
            "sourceKinds": sorted(k),
            "laptopScript": "laptop_script" in k,
            "laptops": len(cur["fleet"].laptops),
        },
    }


LAPTOPS_SHOWN = 300


@router.get("/laptops")
def laptops(http: Request, q: str = "", db: Session = Depends(get_db)):
    # ponytail: built from every source's facts on each read; page in SQL if fleets grow past tens of thousands.
    cur = _current(db, _caller_org(http))
    found = laptop_list(cur["people"], cur["fleet"], cur["stance"], q[:200])
    return {"total": len(found), "laptops": found[:LAPTOPS_SHOWN]}


@router.get("/evidence")
def evidence_for(http: Request, person: Optional[str] = None, laptop: Optional[str] = None, db: Session = Depends(get_db)):
    if bool(person) == bool(laptop):
        raise HTTPException(status_code=422, detail="Ask for one person or one laptop")
    cur = _current(db, _caller_org(http))
    return evidence(cur["assets"], cur["people"], cur["fleet"], cur["stance"], person=person, laptop=laptop)


@router.get("/tools")
def list_tools(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    stance = _stance(db, _caller_org(http))
    return [{"key": s.key, "label": s.label, "vendor": s.vendor, "category": s.category, "stance": stance.get(s.key)} for s in SERVICES]


class StanceBody(BaseModel):
    status: Optional[Literal["approved", "limited", "not_allowed"]] = None  # None clears the stance
    teams: List[str] = Field(default_factory=list, max_length=100)
    sso_required: bool = False
    note: Optional[str] = Field(default=None, max_length=1000)
    tenant_ids: List[str] = Field(default_factory=list, max_length=50)  # company workspace or organisation IDs


_TENANT_ID = re.compile(r"^[A-Za-z0-9_-]{6,80}$")
# Vendors that document a header limiting sign-in to listed company workspaces, when a proxy adds it.
TENANT_HEADERS = {
    "chatgpt": ("ChatGPT-Allowed-Workspace-Id", ("chatgpt.com", "chat.openai.com"), "Workspace ID, in the ChatGPT admin console under workspace settings"),
    "claude": ("anthropic-allowed-org-ids", ("claude.ai", "api.anthropic.com", "console.anthropic.com"), "Organisation ID, in Claude settings under Organisation"),
}


@router.put("/tools/{service_key}")
def set_tool(service_key: str, body: StanceBody, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    hub._ensure_tables()
    org = _caller_org(http)
    if service_key not in _BY_KEY:
        raise HTTPException(status_code=404, detail="Unknown AI service")
    if body.status == "limited" and not [t for t in body.teams if t.strip()]:
        raise HTTPException(status_code=422, detail="Name the teams it is approved for")
    tenant_ids = [t.strip() for t in body.tenant_ids if t.strip()]
    if tenant_ids and service_key not in TENANT_HEADERS:
        raise HTTPException(status_code=422, detail="Only ChatGPT and Claude take company workspace IDs")
    if any(not _TENANT_ID.match(t) for t in tenant_ids):
        raise HTTPException(status_code=422, detail="A workspace ID is letters, digits and dashes only")
    db.execute(text("DELETE FROM governance_approved_ai_tools WHERE org_id = :org AND service_key = :k"), {"org": org, "k": service_key})
    if body.status:
        db.execute(
            text(
                "INSERT INTO governance_approved_ai_tools (id, org_id, service_key, status, teams_json, sso_required, note, updated_by, updated_at, tenant_ids_json) "
                "VALUES (:id, :org, :k, :st, :teams, :sso, :note, :by, :now, :tenants)"
            ),
            {
                "id": str(uuid.uuid4()), "org": org, "k": service_key, "st": body.status, "teams": json.dumps([t.strip() for t in body.teams if t.strip()]),
                "sso": body.sso_required and body.status != "not_allowed", "note": body.note, "by": getattr(who, "user_id", None), "now": _now(),
                "tenants": json.dumps(tenant_ids if body.status in ("approved", "limited") else []),
            },
        )
    db.commit()
    return {"key": service_key, "stance": _stance(db, org).get(service_key)}


def tenant_rules(stance: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Proxy rules that let people sign in only to the company's own ChatGPT and Claude workspaces."""
    rules, missing = [], []
    for svc, (header, hosts, where) in TENANT_HEADERS.items():
        st = stance.get(svc) or {}
        if st.get("status") not in ("approved", "limited"):
            continue
        if st.get("tenantIds"):
            rules.append({"service": svc, "label": _BY_KEY[svc].label, "header": header, "value": ",".join(st["tenantIds"]), "hosts": list(hosts)})
        else:
            missing.append({"service": svc, "label": _BY_KEY[svc].label, "where": where})
    return {"rules": rules, "missing": missing}


@router.get("/tenant-rules")
def get_tenant_rules(http: Request, db: Session = Depends(get_db)):
    hub._ensure_tables()
    return tenant_rules(_stance(db, _caller_org(http)))


class FindingAction(BaseModel):
    key: str = Field(min_length=1, max_length=500)
    reason: Optional[str] = Field(default=None, max_length=1000)
    message: Optional[str] = Field(default=None, max_length=2000)


def _set_state(db: Session, org: str, key: str, who: Any, **cols: Any) -> None:
    sets = ", ".join(f"{c} = :{c}" for c in cols)
    params = {"org": org, "k": key, "by": getattr(who, "user_id", None), "now": _now(), **cols}
    res = db.execute(text(f"UPDATE governance_shadow_states SET {sets}, updated_by = :by, updated_at = :now WHERE org_id = :org AND finding_key = :k"), params)
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="No finding with that key")
    db.commit()


@router.post("/findings/expected")
def mark_expected(body: FindingAction, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    if not (body.reason or "").strip():
        raise HTTPException(status_code=422, detail="Say why it is expected; the reason is kept with the finding")
    _set_state(db, _caller_org(http), body.key, who, status="expected", reason=body.reason.strip())
    return {"key": body.key, "status": "expected"}


@router.post("/findings/reopen")
def reopen(body: FindingAction, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    _set_state(db, _caller_org(http), body.key, who, status="open", reason=None)
    return {"key": body.key, "status": "open"}


@router.post("/findings/nudge")
def nudge(body: FindingAction, http: Request, db: Session = Depends(get_db), who: Any = Depends(org_mutator)):
    """Email the person a finding is about. Only findings that name a person with an email can be sent."""
    from config.settings import settings
    from src.application.services.reviewer_notify import send_in_background

    org = _caller_org(http)
    finding = next((f for f in _current(db, org)["findings"] if f["key"] == body.key), None)
    if not finding:
        raise HTTPException(status_code=404, detail="That finding is no longer open")
    if finding["type"] != "personal_account":
        raise HTTPException(status_code=400, detail="Only a personal-account finding is sent to the person; act on the others yourself")
    to = finding.get("person")
    if not to or "@" not in to:
        raise HTTPException(status_code=400, detail="This finding does not name a person with an email address")
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="Write the message to send")
    if not getattr(settings, "resend_api_key", None):
        raise HTTPException(status_code=503, detail="Email is not set up on this server, so nothing was sent")
    paragraphs = "".join(f'<p style="margin:0 0 12px">{escape(p)}</p>' for p in message.split("\n") if p.strip())
    html = f'<div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:28px;color:#15171a">{paragraphs}</div>'
    send_in_background([to], "About an AI tool on your account", html)
    _set_state(db, org, body.key, who, nudged_at=_now())
    return {"key": body.key, "sentTo": to}
