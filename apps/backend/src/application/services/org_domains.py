"""Email domains and organisation names: which domain an address belongs to, which domains are personal
mail (never an organisation's), and a loose key for spotting organisations whose names only differ in
case, punctuation or a company suffix."""

from __future__ import annotations

import re
from typing import Optional

# Free mail providers: an address here says nothing about which organisation someone belongs to.
PERSONAL_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "msn.com", "yahoo.com", "yahoo.co.in",
    "ymail.com", "icloud.com", "me.com", "mac.com", "aol.com", "proton.me", "protonmail.com", "pm.me", "zoho.com",
    "zohomail.in", "yandex.com", "gmx.com", "gmx.net", "mail.com", "rediffmail.com", "fastmail.com", "tutanota.com",
    "hey.com", "qq.com", "163.com",
})
DOMAIN = re.compile(r"^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
SUFFIXES = re.compile(r"\b(inc|incorporated|llc|ltd|limited|pvt|private|plc|gmbh|corp|corporation|co|company|technologies|technology|tech|security|labs|group|holdings)\b")


def normalize_domain(value: str) -> Optional[str]:
    """'@SQ1.Security ' -> 'sq1.security'; None when it is not a plausible domain."""
    domain = (value or "").strip().lower().lstrip("@").rstrip(".")
    return domain if DOMAIN.match(domain) else None


def email_domain(email: str) -> Optional[str]:
    return normalize_domain(email.rsplit("@", 1)[-1]) if "@" in (email or "") else None


def is_personal(domain: Optional[str]) -> bool:
    return not domain or domain in PERSONAL_DOMAINS


def name_key(name: str) -> str:
    """'SQ1 Security Pvt. Ltd.' and 'sq-1' both become 'sq1': only for warning about likely duplicates."""
    words = SUFFIXES.sub(" ", (name or "").lower())
    return re.sub(r"[^a-z0-9]+", "", words) or re.sub(r"[^a-z0-9]+", "", (name or "").lower())


if __name__ == "__main__":
    assert normalize_domain("@SQ1.Security ") == "sq1.security" and normalize_domain("not a domain") is None
    assert email_domain("kishore.b@sq1.security") == "sq1.security" and is_personal(email_domain("x@gmail.com"))
    assert name_key("SQ1 Security Pvt. Ltd.") == name_key("sq-1") == name_key("SQ1") == "sq1"
    assert name_key("Security") == "security"
    print("org_domains ok")
