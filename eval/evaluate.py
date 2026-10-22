"""Compare configurations: precision / recall / speed.

    python eval/evaluate.py --data eval/data.jsonl                        # regex only
    python eval/evaluate.py --data eval/data.jsonl --gliner               # + GLiNER configs
    python eval/evaluate.py --data eval/data.jsonl --ollama qwen2.5:0.5b  # + LLM configs
"""
import argparse
import json
import time

from scrubin import Scrubber

GROUP = {"ADDRESS": "LOCATION"}   # treat address/location as one family when scoring


def _same(g_label, g_start, g_end, p_label, p_start, p_end):
    return (GROUP.get(g_label, g_label) == GROUP.get(p_label, p_label)
            and g_start < p_end and p_start < g_end)


def score(scrubber, data):
    gold_total = gold_hit = pred_total = pred_hit = 0
    t0 = time.perf_counter()
    for ex in data:
        preds = scrubber.detect(ex["text"])
        gold = ex["entities"]
        for g in gold:
            gold_total += 1
            gold_hit += any(_same(g["label"], g["start"], g["end"], p.label, p.start, p.end) for p in preds)
        for p in preds:
            pred_total += 1
            pred_hit += any(_same(g["label"], g["start"], g["end"], p.label, p.start, p.end) for g in gold)
    dt = time.perf_counter() - t0
    return (gold_hit / max(gold_total, 1), pred_hit / max(pred_total, 1), len(data) / dt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="eval/data.jsonl")
    ap.add_argument("--gliner", action="store_true")
    ap.add_argument("--ollama", metavar="MODEL")
    a = ap.parse_args()
    data = [json.loads(l) for l in open(a.data, encoding="utf-8")]

    configs = [("regex only", lambda: Scrubber(rules=True))]
    if a.gliner:
        configs += [("GLiNER only", lambda: Scrubber(rules=False, engine="gliner")),
                    ("regex + GLiNER", lambda: Scrubber(rules=True, engine="gliner"))]
    if a.ollama:
        configs += [(f"{a.ollama} only", lambda: Scrubber(rules=False, engine="ollama", model_name=a.ollama)),
                    (f"regex + {a.ollama}", lambda: Scrubber(rules=True, engine="ollama", model_name=a.ollama))]

    print(f"{len(data)} samples\n")
    print("| Setup | Recall | Precision | Lines/sec |")
    print("|---|---|---|---|")
    for name, make in configs:
        r, p, speed = score(make(), data)
        print(f"| {name} | {r:.1%} | {p:.1%} | {speed:.1f} |")


if __name__ == "__main__":
    main()