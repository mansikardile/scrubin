---
title: ScrubIN: Scrub Indian PII from Logs and Tickets, 100% Locally
published: true
tags: opensource, hacktoberfest, python, ai
canonical_url: https://github.com/mansikardile/scrubin
cover_image: 
---

Every day, engineers paste production logs and customer support tickets into Slack, Jira, vendor ticketing portals, or cloud LLMs to debug issues. 

More often than not, those logs contain real names, phone numbers, email addresses, and Indian identity data like PAN and Aadhaar numbers. Under India's **Digital Personal Data Protection (DPDP) Act** and **GDPR**, leaking identifiable personal information carries serious compliance and privacy risks.

The common workaround—sending your raw logs to an API or cloud LLM to find PII—ironically leaks the very sensitive data you're trying to protect.

Meet **[ScrubIN](https://github.com/mansikardile/scrubin)**: an open-source, local-first PII scrubber designed specifically for developer workflows.

---

## ⚡ How It Works

ScrubIN combines fast deterministic rules with local open-weight language models via Ollama to scrub PII without any data leaving your machine:

1. **Deterministic Rules & Algorithmic Validators**:
   - High-precision regex patterns for Indian identifiers: PAN, Aadhaar (Verhoeff checksum), Indian mobile numbers, emails, IPv4/IPv6, and JWT/API secret tokens.
   - Algorithmic validation filters out false positives before replacement.
2. **Local Model Layer (Ollama / Qwen2.5)**:
   - For unstructured text and context-dependent entities (Indian names, locations, addresses), a lightweight local model (`qwen2.5:0.5b`) scans the text locally.
3. **Consistent Pseudonymization**:
   - Repeated references to the same entity receive the same placeholder (e.g., `<PERSON_1>`, `<EMAIL_1>`). A log line reading *"<PERSON_1> failed 3 times, then succeeded"* remains fully debuggable.
4. **Reversible Vault (Optional)**:
   - Encrypt original values with an AES key (`--vault map.vault`) to restore logs later if required for audited debugging.

---

## 🔍 Before & After

**Input Log:**
```log
2026-10-21 10:32:11 ERROR payment failed for user Rohan Deshmukh (rohan.d@gmail.com, +91 98765 43210), PAN ABCDE1234F, Aadhaar 2345 6789 0124, token=eyJhbGciOiJIUzI1NiIs.abc123def456.sig789xyz
2026-10-21 10:32:14 WARN retry 1/3 for rohan.d@gmail.com from 203.0.113.42
```

**Cleaned Log:**
```log
2026-10-21 10:32:11 ERROR payment failed for user <PERSON_1> (<EMAIL_1>, <PHONE_1>), PAN <PAN_1>, Aadhaar <AADHAAR_1>, token=<SECRET_1>
2026-10-21 10:32:14 WARN retry 1/3 for <EMAIL_1> from <IP_1>
```

---

## 📊 Benchmark

Evaluated on 50 synthetic Indian log samples containing mixed PII:

| Setup | Recall | Precision | Throughput |
|---|:---:|:---:|:---:|
| **Regex Only** | 67.9% | 96.0% | ~7,800 lines/sec |
| **Regex + Qwen2.5:0.5B** | 91.4% | 88.5% | ~45 lines/sec |

*Evaluated with synthetic test logs using `eval/evaluate.py`.*

---

## 🛠️ Getting Started

```bash
# Install ScrubIN
pip install -e ".[model,vault]"

# Pull the lightweight local model
ollama pull qwen2.5:1.5b

# Scrub a log file
scrubin scrub examples/sample.log --engine ollama

# Pipe directly from kubectl or cat
kubectl logs mypod | scrubin scrub - | pbcopy
```

---

## 🤝 Hacktoberfest & Contributing

ScrubIN is open-source under the MIT license. We welcome contributions during Hacktoberfest! Check out our [good first issues](https://github.com/mansikardile/scrubin/issues) for:
- New Indian identity validators (Voter ID, Passport, Driving Licence)
- Obfuscated PII pattern handling (`user [at] gmail dot com`)
- Integration plugins and UI wrappers

🔗 **GitHub Repository**: [https://github.com/mansikardile/scrubin](https://github.com/mansikardile/scrubin)
