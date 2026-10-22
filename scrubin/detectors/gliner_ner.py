"""Layer 2 (option A): GLiNER, a small open-weight NER model that runs on CPU.

Default: urchade/gliner_small-v2.1 (~166M params, ~0.6 GB, Apache-2.0).
"""
from __future__ import annotations

from typing import List

from ..types import Span
from .base import iter_chunks

LABELS = {
    "person": "PERSON",
    "street address": "ADDRESS",
    "city": "LOCATION",
    "locality": "LOCATION",
    "organization": "ORG",
}


class GlinerDetector:
    def __init__(self, model_name: str = "urchade/gliner_small-v2.1", threshold: float = 0.5):
        try:
            from gliner import GLiNER
        except ImportError as e:
            raise RuntimeError("GLiNER not installed. Run: pip install 'scrubin[model]'") from e
        self.model = GLiNER.from_pretrained(model_name)
        self.threshold = threshold

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []
        for off, chunk in iter_chunks(text, 1000):
            for e in self.model.predict_entities(chunk, list(LABELS), threshold=self.threshold):
                spans.append(Span(off + e["start"], off + e["end"], LABELS[e["label"]], e["text"], "gliner"))
        return spans