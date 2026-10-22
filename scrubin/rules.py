"""Layer 1: regex + validators for anything with a fixed format."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import List

from . import validators as v
from .types import Span


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def _entropy(s: str) -> float:
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in Counter(s).values())


def _ok_aadhaar(s: str) -> bool:
    d = _digits(s)
    return len(d) == 12 and v.verhoeff_valid(d)


def _ok_card(s: str) -> bool:
    d = _digits(s)
    plausible_iin = d[:1] in "3456" or d[:2] in ("81", "82")
    return 13 <= len(d) <= 19 and plausible_iin and v.luhn_valid(d)


def _ok_secret_blob(s: str) -> bool:
    return (any(c.isdigit() for c in s) and any(c.isalpha() for c in s)
            and _entropy(s) >= 4.0)


# (label, compiled regex, capture group to redact, optional validator)
RULES = [
    ("SECRET", re.compile(
        r"(?i)\b(?:token|secret|password|passwd|pwd|api[_-]?key|access[_-]?key|authorization)\b"
        r"\s*[=:]\s*[\"']?(?:Bearer\s+)?([^\s\"',;)]{6,})"), 1, None),
    ("SECRET", re.compile(r"\beyJ[\w-]{5,}\.[\w-]{5,}\.[\w-]*"), 0, None),          # JWT
    ("SECRET", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0, None),                      # AWS
    ("SECRET", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), 0, None),            # GitHub
    ("SECRET", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), 0, None),                   # generic sk- keys
    ("SECRET", re.compile(r"(?<![A-Za-z0-9+/_-])[A-Za-z0-9+_-]{32,}(?![A-Za-z0-9+/_-])"),
     0, _ok_secret_blob),                                                          # high entropy
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), 0, None),
    ("UPI", re.compile(r"\b[\w.-]{2,}@(?:ok(?:sbi|hdfcbank|icici|axis)|ybl|paytm|upi|ibl|axl)\b"), 0, None),
    ("AADHAAR", re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)"), 0, _ok_aadhaar),
    ("CARD", re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)"), 0, _ok_card),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), 0, None),
    ("PHONE", re.compile(r"(?<!\w)(?:\+91[\s-]?|91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)"), 0, None),
    ("IP", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"), 0, None),
    ("IP", re.compile(r"\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b"), 0, None),
]


def detect_rules(text: str) -> List[Span]:
    spans: List[Span] = []
    for label, rx, group, validator in RULES:
        for m in rx.finditer(text):
            start, end = m.start(group), m.end(group)
            value = text[start:end]
            if validator and not validator(value):
                continue
            spans.append(Span(start, end, label, value, "rules"))
    return spans