"""Raw text -> rules -> local model -> merge -> consistent placeholders -> clean text."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from .merge import merge
from .placeholders import PlaceholderMap
from .rules import detect_rules
from .types import Span


class Scrubber:
    def __init__(self, rules: bool = True, engine: Optional[str] = None,
                 model_name: Optional[str] = None, threshold: float = 0.5):
        """engine: None | "gliner" | "ollama". Set rules=False for model-only (for benchmarking)."""
        self.rules = rules
        self.detectors = []
        if engine == "gliner":
            from .detectors.gliner_ner import GlinerDetector
            self.detectors.append(GlinerDetector(model_name or "urchade/gliner_small-v2.1", threshold))
        elif engine == "ollama":
            from .detectors.ollama_llm import OllamaDetector
            self.detectors.append(OllamaDetector(model_name or "qwen2.5:0.5b"))
        elif engine not in (None, "none"):
            raise ValueError(f"unknown engine: {engine}")
        self.placeholders = PlaceholderMap()
        self.last_spans: List[Span] = []

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = detect_rules(text) if self.rules else []
        for d in self.detectors:
            spans += d.detect(text)
        return merge(spans)

    def scrub(self, text: str) -> str:
        spans = self.detect(text)
        self.last_spans = spans
        out, pos = [], 0
        for s in spans:
            out.append(text[pos:s.start])
            out.append(self.placeholders.get(s.label, s.text))
            pos = s.end
        out.append(text[pos:])
        return "".join(out)

    @property
    def mapping(self) -> Dict[str, str]:
        return dict(self.placeholders.reverse)

    def report(self) -> Dict[str, int]:
        return dict(Counter(ph.strip("<>").rsplit("_", 1)[0] for ph in self.placeholders.reverse))