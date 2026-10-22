"""Layer 2 (option B): a small instruction-tuned LLM served by local Ollama.

Default: `ollama pull qwen2.5:0.5b` (~0.4 GB).
Traffic never leaves localhost.
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Dict, List

from ..types import Span
from .base import iter_chunks

TYPES = {"PERSON": "PERSON", "ADDRESS": "ADDRESS", "LOCATION": "LOCATION", "ORG": "ORG"}

PROMPT = (
    "You find personal data in text from logs and support tickets, often Indian names and places. "
    "Return ONLY JSON: {\"entities\": [{\"text\": \"<exact substring>\", \"type\": \"PERSON|LOCATION|ADDRESS|ORG\"}]}. "
    "PERSON = a person's name, LOCATION = city or locality, ADDRESS = street address, ORG = company. "
    "Copy substrings exactly. Ignore emails, numbers, IDs and tokens. "
    "If there is no personal data return {\"entities\": []}.\n\n"
    "Text: Hi, this is Anil from Salem, my parcel is late.\n"
    'Output: {"entities": [{"text": "Anil", "type": "PERSON"}, {"text": "Salem", "type": "LOCATION"}]}\n\n'
    "Text: 2026-10-02 ERROR refund failed for user Farhan Qureshi, shipped to Ludhiana\n"
    'Output: {"entities": [{"text": "Farhan Qureshi", "type": "PERSON"}, {"text": "Ludhiana", "type": "LOCATION"}]}\n\n'
    "Text: 2026-10-02 INFO cache warmed, 1043 keys loaded\n"
    'Output: {"entities": []}\n\n'
    "Text: "
)


class OllamaDetector:
    def __init__(self, model: str = "qwen2.5:1.5b", host: str = "http://localhost:11434"):
        self.model, self.host = model, host

    def _ask(self, chunk: str) -> list:
        payload = {"model": self.model, "prompt": PROMPT + chunk + "\nOutput: ", "stream": False,
                   "format": "json", "options": {"temperature": 0}}
        req = urllib.request.Request(f"{self.host}/api/generate", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
        except OSError as e:
            raise RuntimeError("Cannot reach Ollama. Start it with `ollama serve` "
                               f"and `ollama pull {self.model}`.") from e
        try:
            ents = json.loads(data["response"]).get("entities", [])
            return ents if isinstance(ents, list) else []
        except (ValueError, AttributeError, KeyError):
            return []

    def detect(self, text: str) -> List[Span]:
        # 1) ask the model chunk by chunk (small chunks suit a 0.5B model)
        found: Dict[str, str] = {}
        for _, chunk in iter_chunks(text, 400):
            for ent in self._ask(chunk):
                if not isinstance(ent, dict):
                    continue
                t = ent.get("text")
                label = TYPES.get(str(ent.get("type", "")).upper())
                if isinstance(t, str) and label and len(t.strip()) >= 2 and t in chunk:
                    found[t.strip()] = label
        # 2) propagate: every occurrence of a found entity, anywhere in the text
        spans: List[Span] = []
        for t, label in found.items():
            for m in re.finditer(r"(?<!\w)" + re.escape(t) + r"(?!\w)", text):
                spans.append(Span(m.start(), m.end(), label, t, "ollama"))
        return spans