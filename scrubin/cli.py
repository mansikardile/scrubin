from __future__ import annotations

import argparse
import getpass
import os
import re
import sys

from .pipeline import Scrubber


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _password() -> str:
    return os.environ.get("SCRUBIN_PASSWORD") or getpass.getpass("Vault password: ", stream=sys.stderr)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="scrubin", description="Scrub PII from logs/tickets, locally.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scrub", help="redact PII (file or stdin)")
    s.add_argument("file", nargs="?", default="-")
    s.add_argument("--engine", choices=["none", "gliner", "ollama"], default="none",
                   help="local model for names/addresses (default: rules only)")
    s.add_argument("--model", help="model name override (HF id for gliner, tag for ollama)")
    s.add_argument("--no-rules", action="store_true", help="model only (benchmarking)")
    s.add_argument("--vault", help="save encrypted placeholder mapping to this file")
    s.add_argument("--report", action="store_true", help="print counts to stderr")

    r = sub.add_parser("restore", help="reverse placeholders using a vault")
    r.add_argument("file", nargs="?", default="-")
    r.add_argument("--vault", required=True)

    u = sub.add_parser("ui", help="launch local web UI Studio")
    u.add_argument("--port", type=int, default=8765, help="port to listen on (default: 8765)")

    a = p.parse_args(argv)

    if a.cmd == "scrub":
        sc = Scrubber(rules=not a.no_rules, engine=a.engine, model_name=a.model)
        sys.stdout.write(sc.scrub(_read(a.file)))
        if a.vault:
            from . import vault
            vault.save(sc.mapping, a.vault, _password())
        if a.report:
            print("scrubbed:", sc.report() or "nothing found", file=sys.stderr)
    elif a.cmd == "restore":
        from . import vault
        mapping = vault.load(a.vault, _password())
        sys.stdout.write(re.sub(r"<[A-Z]+_\d+>", lambda m: mapping.get(m.group(0), m.group(0)), _read(a.file)))
    elif a.cmd == "ui":
        from .ui import run_studio
        run_studio(port=a.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())