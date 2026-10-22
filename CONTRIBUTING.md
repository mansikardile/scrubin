# Contributing to ScrubIN

Hacktoberfest contributions welcome. Easy places to start:

- New rules: Voter ID, Driving Licence, Passport, GSTIN, IFSC, vehicle numbers (add to `scrubin/rules.py` + a test)
- Obfuscated formats: `rohan [at] gmail dot com`, phone numbers split across lines
- New detectors: spaCy, Presidio recognisers, other small NER models (add under `scrubin/detectors/`)
- Eval data: harder Indian names/addresses, names that look like words (Rose, Bharat, Mark)
- Local web UI with highlighted detections, Dockerfile, pre-commit hook

Setup: `pip install -e ".[dev]" && pytest`. Every new rule needs a test.