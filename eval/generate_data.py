"""Generate a labelled synthetic test set (fake PII with known positions).

    python eval/generate_data.py --n 200 --out eval/data.jsonl
"""
import argparse
import json
import random
import re
import string

from scrubin.validators import luhn_check_digit, verhoeff_check_digit

FIRST = ["Rohan", "Priya", "Aarav", "Sneha", "Vikram", "Ananya", "Rahul", "Pooja", "Amit", "Neha",
         "Karan", "Meera", "Sanjay", "Divya", "Arjun", "Kavya"]
LAST = ["Deshmukh", "Sharma", "Patil", "Iyer", "Reddy", "Kulkarni", "Gupta", "Nair", "Joshi", "Singh",
        "Mehta", "Bhat"]
PLACES = ["Kothrud", "Baner", "Andheri", "Koramangala", "Salt Lake", "Adyar", "Hinjewadi",
          "Indiranagar", "Powai", "Whitefield"]

TEMPLATES = [
    "{TS} ERROR payment failed for user {PERSON} ({EMAIL}, {PHONE}), PAN {PAN}, Aadhaar {AADHAAR}",
    "{TS} WARN login from {IP} rejected for {EMAIL}",
    "{TS} INFO card {CARD} charged for order #{ORDER}",
    "{TS} DEBUG request token={SECRET} user={PERSON}",
    "{TS} ERROR upstream auth failed key {AWSKEY} ip={IP}",
    "Hi, this is {PERSON} from {LOCATION}, my order #{ORDER} hasn't arrived. Call me on {PHONE}.",
    "Customer {PERSON} reports app crash on checkout. Reach them at {EMAIL}.",
    "{TS} INFO order #{ORDER} delivered to {LOCATION} in 2 attempts",
    "{TS} INFO health check ok latency=120ms order=#{ORDER}",
    "Ticket from {PERSON} ({PHONE}): refund for card {CARD} still pending, Aadhaar {AADHAAR} attached.",
    "{TS} INFO cache warmed, 1043 keys loaded",
]


def digits(rng, n):
    return "".join(rng.choice(string.digits) for _ in range(n))


def gen(kind, rng):
    if kind == "TS":
        return (f"2026-10-{rng.randint(1, 28):02d} {rng.randint(0, 23):02d}:"
                f"{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}", None)
    if kind == "ORDER":
        return digits(rng, 12), None   # random 12 digits: ~10% pass Verhoeff by chance (honest noise)
    if kind == "PERSON":
        return f"{rng.choice(FIRST)} {rng.choice(LAST)}", "PERSON"
    if kind == "LOCATION":
        return rng.choice(PLACES), "LOCATION"
    if kind == "EMAIL":
        return f"{rng.choice(FIRST).lower()}.{rng.choice(LAST)[0].lower()}{rng.randint(1, 99)}@gmail.com", "EMAIL"
    if kind == "PHONE":
        a, b = str(rng.randint(6, 9)) + digits(rng, 4), digits(rng, 5)
        return rng.choice([f"+91 {a} {b}", f"{a}{b}", f"+91-{a}{b}", f"{a} {b}"]), "PHONE"
    if kind == "PAN":
        return ("".join(rng.choice(string.ascii_uppercase) for _ in range(5)) + digits(rng, 4)
                + rng.choice(string.ascii_uppercase)), "PAN"
    if kind == "AADHAAR":
        base = str(rng.randint(2, 9)) + digits(rng, 10)
        n = base + verhoeff_check_digit(base)
        return f"{n[:4]} {n[4:8]} {n[8:]}", "AADHAAR"
    if kind == "CARD":
        base = "4" + digits(rng, 14)
        n = base + luhn_check_digit(base)
        return " ".join(n[i:i + 4] for i in range(0, 16, 4)), "CARD"
    if kind == "IP":
        return ".".join(str(rng.randint(1, 223)) for _ in range(4)), "IP"
    if kind == "SECRET":
        return "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(32)), "SECRET"
    if kind == "AWSKEY":
        return "AKIA" + "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(16)), "SECRET"
    raise KeyError(kind)


def make_sample(rng):
    tpl = rng.choice(TEMPLATES)
    text, ents, pos = "", [], 0
    for m in re.finditer(r"\{(\w+)\}", tpl):
        text += tpl[pos:m.start()]
        val, label = gen(m.group(1), rng)
        if label:
            ents.append({"start": len(text), "end": len(text) + len(val), "label": label})
        text += val
        pos = m.end()
    text += tpl[pos:]
    return {"text": text, "entities": ents}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="eval/data.jsonl")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    with open(a.out, "w", encoding="utf-8") as f:
        for _ in range(a.n):
            f.write(json.dumps(make_sample(rng)) + "\n")
    print(f"wrote {a.n} samples -> {a.out}")