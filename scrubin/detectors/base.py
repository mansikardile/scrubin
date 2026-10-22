from __future__ import annotations

from typing import Iterator, Tuple


def iter_chunks(text: str, max_chars: int = 1000) -> Iterator[Tuple[int, str]]:
    """Yield (offset, chunk), splitting on newlines where possible (models have context limits)."""
    pos, n = 0, len(text)
    while pos < n:
        end = min(pos + max_chars, n)
        if end < n:
            nl = text.rfind("\n", pos, end)
            if nl > pos:
                end = nl + 1
        yield pos, text[pos:end]
        pos = end