"""Consistent placeholders: same value -> same <LABEL_n> everywhere."""
from __future__ import annotations

import re
from typing import Dict, Tuple


def _norm(label: str, text: str) -> str:
    if label in ("AADHAAR", "CARD"):
        return re.sub(r"\D", "", text)
    if label == "PHONE":
        return re.sub(r"\D", "", text)[-10:]
    if label in ("EMAIL", "UPI"):
        return text.lower()
    return " ".join(text.lower().split())


class PlaceholderMap:
    def __init__(self) -> None:
        self._forward: Dict[Tuple[str, str], str] = {}
        self.reverse: Dict[str, str] = {}   # placeholder -> original (this is what the vault stores)
        self._counts: Dict[str, int] = {}

    def get(self, label: str, text: str) -> str:
        key = (label, _norm(label, text))
        ph = self._forward.get(key)
        if ph is None:
            self._counts[label] = self._counts.get(label, 0) + 1
            ph = f"<{label}_{self._counts[label]}>"
            self._forward[key] = ph
            self.reverse[ph] = text
        return ph