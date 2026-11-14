"""Proxy, firewall and gateway logs: which AI services the organisation's traffic reaches.

Works on any export that names the destination host: Zscaler, Netskope, Palo Alto, Squid,
an API gateway or CloudTrail-style JSON lines. JSON lines and CSV with a header also give
the user or client per request; plain text lines give request counts only.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set

from . import asset
from .catalog import SERVICES, asset_kind, by_host

_HOST = re.compile(r"(?<![\w.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}(?![\w-])", re.I)
_USER_KEYS = ("user", "username", "user_name", "userName", "src_user", "login", "email", "client_ip", "src_ip", "source_ip", "clientIP")
MAX_USERS_LISTED = 25


def _user_of(row: Dict[str, Any]) -> Optional[str]:
    for k in _USER_KEYS:
        v = row.get(k)
        if isinstance(v, dict):  # e.g. CloudTrail userIdentity-style nesting
            v = v.get("arn") or v.get("userName")
        if v:
            return str(v)
    return None


def _rows(text: str) -> Iterable[tuple]:
    """(line text, user or None) for each record, whatever the format."""
    lines = text.splitlines()
    first = next((l for l in lines if l.strip()), "")
    if first.lstrip().startswith("{"):
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                yield line, None
                continue
            yield (json.dumps(row) if isinstance(row, dict) else line), (_user_of(row) if isinstance(row, dict) else None)
        return
    if "," in first and not _HOST.search(first) and any(k.lower() in first.lower() for k in ("host", "url", "dest", "domain", "uri")):
        for row in csv.DictReader(io.StringIO(text)):
            yield ",".join(str(v) for v in row.values() if v), _user_of(row)
        return
    for line in lines:
        yield line, None


def parse(text: str) -> List[Dict[str, Any]]:
    hits: Dict[str, int] = defaultdict(int)
    users: Dict[str, Set[str]] = defaultdict(set)
    hosts: Dict[str, Set[str]] = defaultdict(set)
    total = 0
    for line, user in _rows(text):
        total += 1
        seen = set()
        for m in _HOST.finditer(line):
            s = by_host(m.group(0))
            if s and s.key not in seen:  # count a request once even if the host repeats in the line
                seen.add(s.key)
                hits[s.key] += 1
                hosts[s.key].add(m.group(0).lower())
                if user:
                    users[s.key].add(user)
    by_key = {s.key: s for s in SERVICES}
    out = []
    for key, n in sorted(hits.items(), key=lambda kv: -kv[1]):
        s = by_key[key]
        u = sorted(users[key])
        out.append(
            asset(
                f"service:{key}",
                s.label,
                asset_kind(s),
                {
                    "vendor": s.vendor,
                    "category": s.category,
                    "requests": n,
                    "hosts": sorted(hosts[key]),
                    "distinct_users": len(u) if u else None,
                    "users": u[:MAX_USERS_LISTED],
                    "log_records_read": total,
                    "signal": "network traffic",
                },
                tier="low" if s.category == "dev" else "medium",
            )
        )
    return out
