---
name: New PII Rule Proposal
about: Suggest or implement detection for a new identifier (e.g., Voter ID, Driving Licence, etc.)
title: "[RULE]: Add support for <Entity Name>"
labels: ["enhancement", "good first issue", "hacktoberfest"]
assignees: ''
---

### Proposed Entity
- **Entity Type / Label**: (e.g. `VOTER_ID`, `PASSPORT`, `DRIVING_LICENCE`, `IFSC`)
- **Country / Jurisdiction**: (e.g. India)

### Format & Pattern Specification
- **Expected Pattern / Format**: (e.g. 3 uppercase letters followed by 7 digits)
- **Sample values (synthetic/anonymized only)**:
  - Valid: `ABC1234567`
  - Invalid / Edge case: `AB1234567`

### Algorithmic Validation (if applicable)
Does this identifier have a checksum algorithm (like Luhn, Verhoeff, or ISO 7064)?

### Checklist
- [ ] Regex rule can be added to `scrubin/rules.py`
- [ ] Validator function can be added to `scrubin/validators.py`
- [ ] Unit tests added to `tests/test_validators.py`
