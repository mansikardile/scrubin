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


def score(scrubber, data, breakdown=False):
    gold_total = gold_hit = pred_total = pred_hit = 0
    by_entity = {}  # label -> {"gold": 0, "hit": 0, "misses": []}
    t0 = time.perf_counter()
    for ex in data:
        preds = scrubber.detect(ex["text"])
        gold = ex["entities"]
        for g in gold:
            lbl = GROUP.get(g["label"], g["label"])
            if lbl not in by_entity:
                by_entity[lbl] = {"gold": 0, "hit": 0, "misses": []}
            by_entity[lbl]["gold"] += 1
            gold_total += 1
            hit = any(_same(g["label"], g["start"], g["end"], p.label, p.start, p.end) for p in preds)
            if hit:
                gold_hit += 1
                by_entity[lbl]["hit"] += 1
            else:
                val = ex["text"][g["start"]:g["end"]]
                if len(by_entity[lbl]["misses"]) < 3:
                    by_entity[lbl]["misses"].append(val)
        for p in preds:
            pred_total += 1
            pred_hit += any(_same(g["label"], g["start"], g["end"], p.label, p.start, p.end) for g in gold)
    dt = time.perf_counter() - t0
    res = (gold_hit / max(gold_total, 1), pred_hit / max(pred_total, 1), len(data) / dt)
    return (res, by_entity) if breakdown else res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="eval/data.jsonl")
    ap.add_argument("--gliner", action="store_true")
    ap.add_argument("--ollama", metavar="MODEL")
    ap.add_argument("--breakdown", action="store_true", help="show per-entity recall and sample false negatives")
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
    breakdowns = {}
    for name, make in configs:
        if a.breakdown:
            (r, p, speed), ent_stats = score(make(), data, breakdown=True)
            breakdowns[name] = ent_stats
        else:
            r, p, speed = score(make(), data)
        print(f"| {name} | {r:.1%} | {p:.1%} | {speed:.1f} |")

    if a.breakdown:
        print("\n### Per-Entity Recall & False Negatives Breakdown\n")
        all_labels = sorted(set(l for b in breakdowns.values() for l in b.keys()))
        header = "| Entity | Count | " + " | ".join(f"{name} Recall" for name in breakdowns.keys()) + " | Sample Misses (Rules) |"
        print(header)
        print("|" + "---|"*len(header.split("|")[1:-1]))
        rules_misses = breakdowns.get("regex only", {})
        for lbl in all_labels:
            cnt = next((b[lbl]["gold"] for b in breakdowns.values() if lbl in b), 0)
            recalls = []
            for name in breakdowns.keys():
                b = breakdowns[name].get(lbl, {"hit": 0, "gold": 1})
                rec = b["hit"] / max(b["gold"], 1)
                recalls.append(f"{rec:.1%}")
            sample_miss = ", ".join(f'"{m}"' for m in rules_misses.get(lbl, {}).get("misses", [])) or "None"
            print(f"| {lbl} | {cnt} | " + " | ".join(recalls) + f" | {sample_miss} |")


if __name__ == "__main__":
    main()