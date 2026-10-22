# Contributing to ScrubIN

Thank you for your interest in contributing! ScrubIN is an open-source project participating in **Hacktoberfest**. 

## 🎃 Hacktoberfest Participation
- Look for issues labeled [`good first issue`](https://github.com/mansikardile/scrubin/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) and [`hacktoberfest`](https://github.com/mansikardile/scrubin/issues?q=is%3Aissue+is%3Aopen+label%3Ahacktoberfest).
- All legitimate pull requests adding rules, detectors, tests, or documentation improvements are welcome!

## 💡 Great Places to Start
1. **New Indian Identifier Rules**:
   - Voter ID (EPIC), Indian Passport, Driving Licence, GSTIN, Vehicle registration numbers, IFSC codes.
   - Add regex patterns in `scrubin/rules.py` and checksum / algorithmic validation in `scrubin/validators.py`.
2. **Handling Obfuscated Formats**:
   - `rohan [at] gmail dot com`, `rohan (at) domain.com`.
   - Phone numbers split across lines or written in words.
3. **New Detectors & NER Backends**:
   - Microsoft Presidio integration, spaCy recognizers.
   - Add new backends under `scrubin/detectors/`.
4. **Evaluation Datasets**:
   - Harder Indian names, locations, and names that look like standard English words (e.g. "Rose", "Bharat", "Mark", "May").
5. **Developer Tooling**:
   - Pre-commit hooks, Docker container, local web UI with visual entity highlighting.

---

## 🛠️ Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mansikardile/scrubin.git
   cd scrubin
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies in editable mode**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run the test suite**:
   ```bash
   pytest -q
   ```

---

## 📝 Rules for Submissions
- **Synthetic Data Only**: NEVER use real personal data in test cases, fixtures, or examples.
- **Test Coverage**: Every new detector or validator must have accompanying unit tests in `tests/`.
- **Keep it Local**: ScrubIN is local-first. We do not accept features that call external cloud APIs to detect PII.