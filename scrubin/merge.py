"""Overlap resolution.

Priority: rules beat the model; inside one source the longer span wins;
ties are broken by LABEL_RANK. Result is sorted and non-overlapping.
"""
from __future__ import annotations

import bisect
from typing import List

from .types import Span

LABEL_RANK = {l: i for i, l in enumerate(
    ["SECRET", "AADHAAR", "CARD", "PAN", "EMAIL", "UPI", "PHONE", "IP", "PERSON", "ADDRESS", "LOCATION", "ORG"])}


def merge(spans: List[Span]) -> List[Span]:
    ordered = sorted(spans, key=lambda s: (
        0 if s.source == "rules" else 1, -(s.end - s.start), LABEL_RANK.get(s.label, 99), s.start))
    starts: List[int] = []
    taken: List[Span] = []
    for s in ordered:
        i = bisect.bisect_left(starts, s.start)
        if i > 0 and taken[i - 1].end > s.start:
            continue
        if i < len(taken) and taken[i].start < s.end:
            continue
        starts.insert(i, s.start)
        taken.insert(i, s)
    return taken