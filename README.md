# ScrubIN: scrub PII from logs and tickets, locally

[![CI](https://github.com/mansikardile/scrubin/actions/workflows/ci.yml/badge.svg)](https://github.com/mansikardile/scrubin/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Paste logs into Slack, vendor portals or cloud LLMs without leaking people's data.
Rules + a small open-weight model that runs on your machine. Nothing is sent to the cloud.

**Before**
```
2026-10-21 10:32:11 ERROR payment failed for user Rohan Deshmukh (rohan.d@gmail.com, +91 98765 43210),
PAN ABCDE1234F, Aadhaar 2345 6789 0124, token=eyJhbGciOiJIUzI1NiIs.abc123def456.sig789xyz
```
**After**
```
2026-10-21 10:32:11 ERROR payment failed for user <PERSON_1> (<EMAIL_1>, <PHONE_1>),
PAN <PAN_1>, Aadhaar <AADHAAR_1>, token=<SECRET_1>
```
Same person => same placeholder, so "<PERSON_1> failed 3 times, then succeeded" is still debuggable.
Relevant to India's DPDP Act and GDPR.

## Install
```bash
pip install -e ".[model,vault]"
ollama pull qwen2.5:1.5b
```

## Use
```bash
scrubin scrub examples/sample.log                      # rules only
scrubin scrub examples/sample.log --engine ollama      # + Qwen2.5 1.5B
scrubin scrub examples/sample.log --engine gliner      # + GLiNER
kubectl logs mypod | scrubin scrub - | pbcopy          # pipe mode
scrubin scrub app.log --vault map.vault > clean.log
scrubin restore clean.log --vault map.vault
```

## Benchmark
Evaluated on 50 synthetic Indian log samples containing mixed PII (PAN, Aadhaar, names, emails, phones, IPs, secrets, locations):

| Setup | Recall | Precision | Lines/sec |
|---|---|---|---|
| regex only | 67.9% | 96.0% | ~7,800 |
| regex + Qwen2.5:0.5B | 91.4% | 88.5% | ~45 |

*Evaluated with `python eval/evaluate.py`.*

## Honest limitations
No scrubber is 100%. Obfuscated formats, split lines, names that look like words, and Indian
names/addresses in free text can slip through. Have a human check high-risk data.

## License
MIT