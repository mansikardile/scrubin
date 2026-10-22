from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    label: str
    text: str
    source: str  # "rules" | "gliner" | "ollama"