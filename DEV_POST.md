---
title: ScrubIN: Scrub Indian PII from Logs and Tickets, 100% Locally
published: true
tags: opensource, hacktoberfest, python, ai
canonical_url: https://github.com/mansikardile/scrubin
cover_image: 
---

Every day, engineers paste production logs and customer support tickets into Slack, Jira, vendor ticketing portals, or cloud LLMs to debug issues. 

More often than not, those logs contain real names, phone numbers, email addresses, and Indian identity data like PAN and Aadhaar numbers. Under India's **Digital Personal Data Protection (DPDP) Act** and **GDPR**, leaking identifiable personal information carries serious compliance and privacy risks.

The common workaround—sending raw logs to an external API or cloud LLM to find PII—ironically leaks the very sensitive data you're trying to protect.

Meet **[ScrubIN](https://github.com/mansikardile/scrubin)**: an open-source, local-first PII scrubber designed specifically for developer workflows.

---

## ⚡ Why AI Matters: Rules vs. Hybrid Pipeline

Deterministic regular expressions are ultra-fast (~15,000 lines/sec) and catch structured identifiers (PAN, Aadhaar, emails, phones, tokens) with near-zero false alarms. But **rules alone cannot understand contextual free text**, such as Indian customer names and locations in support tickets:

| Text Fragment | Regex Rules Only | Hybrid: Rules + Qwen2.5 1.5B |
|---|---|---|
| `user Rohan Deshmukh (rohan.d@gmail.com)` | `user Rohan Deshmukh (<EMAIL_1>)` ❌ *Name leaked* | `user <PERSON_1> (<EMAIL_1>)` ✅ |
| `shipped to Kothrud, Pune` | `shipped to Kothrud, Pune` ❌ *Address leaked* | `shipped to <LOCATION_1>, Pune` ✅ |
| `PAN ABCDE1234F, Aadhaar 2345 6789 0124` | `PAN <PAN_1>, Aadhaar <AADHAAR_1>` ✅ | `PAN <PAN_1>, Aadhaar <AADHAAR_1>` ✅ |

---

## 🏗️ Architecture

1. **Deterministic Rules & Algorithmic Validators**:
   - High-precision regex patterns for Indian identifiers: PAN, Aadhaar (Verhoeff checksum), Indian mobile numbers, emails, IPv4/IPv6, and JWT/API secret tokens.
   - Algorithmic validation filters out false positives before replacement.
2. **Local Model Layer (Ollama / Qwen2.5 1.5B)**:
   - For unstructured text and context-dependent entities (Indian names, locations, addresses), a lightweight local model (`qwen2.5:1.5b`) scans the text locally via Ollama.
3. **Consistent Pseudonymization**:
   - Repeated references to the same entity receive the same placeholder (e.g., `<PERSON_1>`, `<EMAIL_1>`). A log line reading *"<PERSON_1> failed 3 times, then succeeded"* remains fully debuggable.
4. **Reversible Vault (Optional)**:
   - Encrypt original values with an AES-256-GCM key (`--vault map.vault`) to restore logs later if required for audited debugging.
5. **Local Web Studio**:
   - Built-in zero-dependency web interface (`scrubin ui`) for live interactive scrubbing, side-by-side comparison, and visual entity counts.

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

## 📊 Benchmark & Per-Entity Breakdown

Evaluated on 50 synthetic Indian log samples containing mixed PII across 8 categories:

| Setup | Overall Recall | Overall Precision | Throughput |
|---|:---:|:---:|:---:|
| **Regex Only** | 67.9% | 96.0% | **~15,500 lines/sec** |
| **Hybrid (Regex + Qwen2.5:1.5B)** | **100.0%** | **94.6%** | local inference |

### Per-Entity Breakdown

| Entity Type | Count | Regex Recall | Hybrid Recall | Guard Mechanism |
|---|:---:|:---:|:---:|---|
| **AADHAAR** | 8 | 100.0% | **100.0%** | Verhoeff Checksum validation |
| **CARD** | 9 | 100.0% | **100.0%** | Luhn Checksum validation |
| **EMAIL** | 15 | 100.0% | **100.0%** | RFC format validation |
| **IP (v4/v6)** | 12 | 100.0% | **100.0%** | Range checks |
| **PAN** | 5 | 100.0% | **100.0%** | Format pattern |
| **PHONE** | 15 | 100.0% | **100.0%** | Mobile prefixes (`+91`) |
| **SECRET** | 8 | 100.0% | **100.0%** | JWT & AWS Access Keys |
| **PERSON** | 21 | 0.0% | **100.0%** | Contextual NER via Qwen2.5 |
| **LOCATION** | 13 | 0.0% | **100.0%** | Contextual NER via Qwen2.5 |

---

## 🛠️ Getting Started

```bash
# Install ScrubIN
pip install -e ".[model,vault]"

# Pull the lightweight local model
ollama pull qwen2.5:1.5b

# Launch the interactive local studio
scrubin ui

# Or scrub directly from terminal / pipe
scrubin scrub examples/sample.log --engine ollama
kubectl logs mypod | scrubin scrub - | pbcopy
```

---

## 🤝 Hacktoberfest & Contributing

ScrubIN is open-source under the MIT license. We welcome contributions during Hacktoberfest! Check out our [good first issues](https://github.com/mansikardile/scrubin/issues) for:
- New Indian identity validators (Voter ID, Passport, Driving Licence)
- Obfuscated PII pattern handling (`user [at] gmail dot com`)
- Integration plugins and UI wrappers

🔗 **GitHub Repository**: [https://github.com/mansikardile/scrubin](https://github.com/mansikardile/scrubin)
