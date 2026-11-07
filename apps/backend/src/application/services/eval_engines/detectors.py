"""Pattern detectors shared by the engines: personal data, secrets, and instructions hidden in text.

Each detector is a regex plus, where a checksum exists, a validator, so a twelve-digit
number only counts as an Aadhaar when its Verhoeff check digit holds.
"""

import re
from typing import Callable, Dict, Iterable, List, Optional, Tuple

# --- checksums ---------------------------------------------------------------

_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7], [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3], [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7], [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def verhoeff(digits: str) -> bool:
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(ch)]]
    return c == 0


def luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total, alt = total + d, not alt
    return total % 10 == 0


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


Detector = Tuple[str, "re.Pattern[str]", Optional[Callable[[str], bool]]]

PERSONAL: List[Detector] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), None),
    ("phone", re.compile(r"(?<!\d)(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)|(?<!\w)\+\d{1,3}[\s-]?\d{6,12}(?!\d)"), None),
    ("aadhaar", re.compile(r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"), lambda m: verhoeff(_digits(m))),
    ("pan", re.compile(r"\b[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]\b"), None),
    ("ifsc", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"), None),
    ("payment_card", re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"), lambda m: 13 <= len(_digits(m)) <= 19 and luhn(_digits(m))),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"), None),
    ("passport_in", re.compile(r"\b[A-PR-WY][1-9]\d{6}\b"), None),
    ("ip_address", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"), None),
]

SECRETS: List[Detector] = [
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), None),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"), None),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), None),
    ("api_key", re.compile(r"\b(?:sk|pk|rk)[-_](?:live|test|ant|proj)?[-_]?[A-Za-z0-9_-]{20,}\b"), None),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), None),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"), None),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), None),
    ("connection_string", re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s@/]+@[^\s]+", re.I), None),
    ("password_assignment", re.compile(r"(?i)\b(?:password|passwd|pwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\"]{8,}"), None),
]

# Instructions planted in data, documents, tool descriptions or memories.
INSTRUCTIONS: List[Detector] = [
    ("override", re.compile(r"(?i)\b(?:ignore|disregard|forget|override)\b.{0,40}\b(?:previous|prior|above|earlier|all|system)\b.{0,20}\b(?:instructions?|prompts?|rules?|messages?)"), None),
    ("role_change", re.compile(r"(?i)\byou are (?:now|no longer)\b|\bact as (?:an? )?(?:unrestricted|jailbroken|dan)\b|\bdeveloper mode\b"), None),
    ("fake_turn", re.compile(r"(?im)^\s*(?:system|assistant)\s*:|<\|(?:im_start|system|endoftext)\|>|\[/?INST\]|</?system>"), None),
    ("concealment", re.compile(r"(?i)\b(?:do not|don't|never) (?:tell|inform|reveal|mention|show)(?: this)? (?:to )?(?:the )?user\b"), None),
    ("exfiltration", re.compile(r"(?i)!\[[^\]]*\]\(https?://[^)]*\?[^)]*=|\b(?:send|post|upload|forward)\b.{0,40}\b(?:to|at)\b\s*https?://"), None),
    ("hidden_markup", re.compile(r"(?is)<!--.*?-->|display\s*:\s*none|font-size\s*:\s*0|color\s*:\s*(?:white|#fff(?:fff)?)\b"), None),
    ("invisible_text", re.compile("[​-‏‪-‮⁠-⁤﻿\U000e0000-\U000e007f]"), None),
    ("sensitive_path", re.compile(r"(?i)~/\.(?:ssh|aws|config)|/etc/(?:passwd|shadow)|\bid_rsa\b|\.env\b"), None),
]


def scan(text: str, detectors: Iterable[Detector]) -> List[Tuple[str, str]]:
    """(category, matched text) for every validated hit."""
    hits = []
    for name, pattern, valid in detectors:
        for m in pattern.finditer(text):
            if valid is None or valid(m.group(0)):
                hits.append((name, m.group(0)))
    return hits


def mask(value: str) -> str:
    """Enough to find the hit, not enough to reuse it."""
    v = value.strip()
    return v if len(v) <= 6 else f"{v[:3]}...{v[-2:]}"


def counts(hits: Iterable[Tuple[str, str]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for name, _ in hits:
        out[name] = out.get(name, 0) + 1
    return out
