"""Local Ollama detector for contextual entities (names, locations, addresses).

Combines lightweight local LLMs with validated, chunk-relative entity spans.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import List

from ..types import Span
from .base import iter_chunks

TYPES = {
    "PERSON": "PERSON",
    "ADDRESS": "ADDRESS",
    "LOCATION": "LOCATION",
    "ORG": "ORG",
}

PROMPT = (
    "Identify personal names, physical addresses, locations, and organization names in text from logs and support tickets. "
    'Return ONLY JSON: {"entities": [{"text": "<exact substring>", "type": "PERSON|LOCATION|ADDRESS|ORG"}]}. '
    "PERSON = a person's name, LOCATION = city or locality, ADDRESS = street address, ORG = company. "
    "Copy substrings exactly. Do not include surrounding words. Ignore emails, numbers, IDs, and tokens. "
    'If there is no personal data return {"entities": []}.\n\n'
    "Text: Hi, this is Anil from Salem, my parcel is late.\n"
    'Output: {"entities": [{"text": "Anil", "type": "PERSON"}, {"text": "Salem", "type": "LOCATION"}]}\n\n'
    "Text: 2026-10-02 ERROR refund failed for user Farhan Qureshi, shipped to Ludhiana\n"
    'Output: {"entities": [{"text": "Farhan Qureshi", "type": "PERSON"}, {"text": "Ludhiana", "type": "LOCATION"}]}\n\n'
    "Text: 2026-10-02 INFO cache warmed, 1043 keys loaded\n"
    'Output: {"entities": []}\n\n'
    "Text: "
)


class OllamaDetector:
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        host: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _ask(self, chunk: str) -> list:
        payload = {
            "model": self.model,
            "prompt": PROMPT + chunk + "\nOutput: ",
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout
            ) as response:
                data = json.load(response)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.host}. "
                f"Start Ollama and pull the model {self.model!r}."
            ) from exc

        try:
            result = json.loads(data["response"])
        except (ValueError, TypeError, KeyError):
            return []

        entities = result.get("entities", [])
        return entities if isinstance(entities, list) else []

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []

        for offset, chunk in iter_chunks(text, 400):
            for entity in self._ask(chunk):
                if not isinstance(entity, dict):
                    continue

                label = TYPES.get(str(entity.get("type", "")).upper())
                value = entity.get("text")
                start = entity.get("start")
                end = entity.get("end")

                if label is None or not isinstance(value, str):
                    continue
                value = value.strip()
                if not value or len(value) < 2 or value not in chunk:
                    continue

                if start is not None or end is not None:
                    # Explicit offsets provided: validate them strictly
                    if not isinstance(start, int) or isinstance(start, bool):
                        continue
                    if not isinstance(end, int) or isinstance(end, bool):
                        continue
                    if not (0 <= start < end <= len(chunk)):
                        continue
                    if chunk[start:end] != value:
                        continue
                    spans.append(
                        Span(
                            offset + start,
                            offset + end,
                            label,
                            value,
                            "ollama",
                        )
                    )
                else:
                    # Locate occurrences within this chunk
                    pattern = r"(?<!\w)" + re.escape(value) + r"(?!\w)"
                    for m in re.finditer(pattern, chunk):
                        spans.append(
                            Span(
                                offset + m.start(),
                                offset + m.end(),
                                label,
                                value,
                                "ollama",
                            )
                        )

        return spans
