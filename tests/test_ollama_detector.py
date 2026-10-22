
import json

from scrubin.detectors.ollama_llm import OllamaDetector


def test_detector_uses_chunk_relative_offsets(monkeypatch):
    detector = OllamaDetector()
    monkeypatch.setattr(
        detector,
        "_ask",
        lambda chunk: [
            {
                "text": "Anil",
                "type": "PERSON",
                "start": 12,
                "end": 16,
            }
        ],
    )

    text = "Hi, this is Anil from Salem."
    spans = detector.detect(text)

    assert len(spans) == 1
    assert text[spans[0].start:spans[0].end] == "Anil"
    assert spans[0].label == "PERSON"


def test_detector_rejects_invalid_offsets(monkeypatch):
    detector = OllamaDetector()
    monkeypatch.setattr(
        detector,
        "_ask",
        lambda chunk: [
            {
                "text": "Anil",
                "type": "PERSON",
                "start": 0,
                "end": 4,
            }
        ],
    )

    # The claimed offsets do not point to "Anil".
    assert detector.detect("This is Anil.") == []


def test_detector_does_not_propagate_to_other_chunks(monkeypatch):
    detector = OllamaDetector()

    def fake_ask(chunk):
        if "May" in chunk:
            return [
                {
                    "text": "May",
                    "type": "PERSON",
                    "start": chunk.index("May"),
                    "end": chunk.index("May") + 3,
                }
            ]
        return []

    monkeypatch.setattr(detector, "_ask", fake_ask)

    text = "May contacted support.\n" + ("x" * 410) + "\nMay arrived in May."
    spans = detector.detect(text)

    occurrences = [text[s.start:s.end] for s in spans]
    assert occurrences.count("May") == 2
