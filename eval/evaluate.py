
"""Evaluate ScrubIN detection quality.

Examples:
    python eval/evaluate.py --data eval/data.jsonl
    python eval/evaluate.py --data eval/data.jsonl --gliner
    python eval/evaluate.py --data eval/data.jsonl --ollama qwen2.5:1.5b
    python eval/evaluate.py --data eval/data.jsonl --breakdown

Metrics:
- Recall: exact-span, compatible-label matches / gold entities.
- Precision: exact-span, compatible-label matches / predicted entities.
- Complete coverage: gold spans fully covered by a compatible prediction.
- Lines/sec: input examples processed per second, not log lines.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from scrubin import Scrubber

GROUP = {"ADDRESS": "LOCATION"}


def compatible_labels(gold_label: str, pred_label: str) -> bool:
    return GROUP.get(gold_label, gold_label) == GROUP.get(
        pred_label, pred_label
    )


def exact_match(gold: dict, pred) -> bool:
    return (
        compatible_labels(gold["label"], pred.label)
        and gold["start"] == pred.start
        and gold["end"] == pred.end
    )


def fully_covers(gold: dict, pred) -> bool:
    """True if a compatible prediction covers the entire gold span."""
    return (
        compatible_labels(gold["label"], pred.label)
        and pred.start <= gold["start"]
        and pred.end >= gold["end"]
    )


def score(scrubber, data, breakdown=False):
    gold_total = 0
    pred_total = 0
    exact_hits = 0
    covered_gold = 0
    by_entity = {}

    start_time = time.perf_counter()

    for example in data:
        text = example["text"]
        gold_entities = example["entities"]
        predictions = scrubber.detect(text)

        gold_total += len(gold_entities)
        pred_total += len(predictions)

        for gold in gold_entities:
            label = GROUP.get(gold["label"], gold["label"])
            stats = by_entity.setdefault(
                label,
                {"gold": 0, "exact": 0, "covered": 0, "misses": []},
            )
            stats["gold"] += 1

            exact = any(exact_match(gold, pred) for pred in predictions)
            covered = any(
                fully_covers(gold, pred) for pred in predictions
            )

            if exact:
                exact_hits += 1
                stats["exact"] += 1
            else:
                if len(stats["misses"]) < 5:
                    stats["misses"].append(
                        text[gold["start"]:gold["end"]]
                    )

            if covered:
                covered_gold += 1
                stats["covered"] += 1

    elapsed = max(time.perf_counter() - start_time, 1e-9)

    result = {
        "recall": exact_hits / gold_total if gold_total else 0.0,
        "precision": exact_hits / pred_total if pred_total else 0.0,
        "complete_coverage": (
            covered_gold / gold_total if gold_total else 0.0
        ),
        "examples_per_second": len(data) / elapsed,
        "gold_count": gold_total,
        "prediction_count": pred_total,
    }

    if breakdown:
        return result, by_entity
    return result


def load_data(path: str) -> list:
    data_path = Path(path)
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    examples = []
    with data_path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                example = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {data_path}:{line_number}"
                ) from exc

            if not isinstance(example.get("text"), str):
                raise ValueError(
                    f"Missing string 'text' at line {line_number}"
                )
            if not isinstance(example.get("entities"), list):
                raise ValueError(
                    f"Missing list 'entities' at line {line_number}"
                )

            text = example["text"]
            for entity in example["entities"]:
                if not isinstance(entity, dict):
                    raise ValueError(
                        f"Invalid entity at line {line_number}"
                    )
                label = entity.get("label")
                start = entity.get("start")
                end = entity.get("end")
                if (
                    not isinstance(label, str)
                    or not isinstance(start, int)
                    or isinstance(start, bool)
                    or not isinstance(end, int)
                    or isinstance(end, bool)
                    or not (0 <= start < end <= len(text))
                ):
                    raise ValueError(
                        f"Invalid entity offsets at line {line_number}: "
                        f"{entity!r}"
                    )

            examples.append(example)

    if not examples:
        raise ValueError(f"No examples found in {data_path}")

    return examples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="eval/data.jsonl")
    parser.add_argument("--gliner", action="store_true")
    parser.add_argument("--ollama", metavar="MODEL")
    parser.add_argument("--breakdown", action="store_true")
    args = parser.parse_args()

    data = load_data(args.data)

    configs = [
        ("regex only", lambda: Scrubber(rules=True)),
    ]

    if args.gliner:
        configs.extend([
            (
                "GLiNER only",
                lambda: Scrubber(rules=False, engine="gliner"),
            ),
            (
                "regex + GLiNER",
                lambda: Scrubber(rules=True, engine="gliner"),
            ),
        ])

    if args.ollama:
        configs.extend([
            (
                f"{args.ollama} only",
                lambda: Scrubber(
                    rules=False,
                    engine="ollama",
                    model_name=args.ollama,
                ),
            ),
            (
                f"regex + {args.ollama}",
                lambda: Scrubber(
                    rules=True,
                    engine="ollama",
                    model_name=args.ollama,
                ),
            ),
        ])

    print(f"{len(data)} examples\n")
    print(
        "| Setup | Exact recall | Exact precision | "
        "Complete coverage | Examples/sec |"
    )
    print("|---|---:|---:|---:|---:|")

    all_breakdowns = {}

    for name, make_scrubber in configs:
        result = score(
            make_scrubber(),
            data,
            breakdown=args.breakdown,
        )

        if args.breakdown:
            result, breakdown = result
            all_breakdowns[name] = breakdown

        print(
            f"| {name} "
            f"| {result['recall']:.1%} "
            f"| {result['precision']:.1%} "
            f"| {result['complete_coverage']:.1%} "
            f"| {result['examples_per_second']:.1f} |"
        )

    if args.breakdown:
        print("\n### Per-entity results\n")
        for name, stats in all_breakdowns.items():
            print(f"\n#### {name}\n")
            print("| Entity | Gold | Exact recall | Full coverage | Sample misses |")
            print("|---|---:|---:|---:|---|")
            for label, item in sorted(stats.items()):
                total = item["gold"]
                recall = item["exact"] / total if total else 0.0
                coverage = item["covered"] / total if total else 0.0
                misses = ", ".join(
                    f"`{value}`" for value in item["misses"]
                ) or "None"
                print(
                    f"| {label} | {total} | {recall:.1%} "
                    f"| {coverage:.1%} | {misses} |"
                )


if __name__ == "__main__":
    main()
