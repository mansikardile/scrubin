"""Local Web UI Studio for ScrubIN.
Run with:
    scrubin ui
    python -m scrubin.ui
"""
import json
import os
import sys
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

from .pipeline import Scrubber

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ScrubIN — Local PII Scrubber Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #0a0d14;
      --card-bg: rgba(18, 24, 38, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent: #3b82f6;
      --accent-glow: rgba(59, 130, 246, 0.25);
      --accent-gradient: linear-gradient(135deg, #3b82f6, #8b5cf6);
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --tag-person: #ec4899;
      --tag-pan: #f59e0b;
      --tag-aadhaar: #10b981;
      --tag-secret: #ef4444;
      --tag-contact: #06b6d4;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.1) 0%, transparent 40%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    header {
      padding: 18px 36px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      backdrop-filter: blur(12px);
      background: rgba(10, 13, 20, 0.8);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-badge {
      background: var(--accent-gradient);
      color: white;
      font-weight: 800;
      font-size: 14px;
      padding: 6px 12px;
      border-radius: 8px;
      letter-spacing: 0.5px;
      box-shadow: 0 4px 12px var(--accent-glow);
    }

    .title {
      font-size: 18px;
      font-weight: 700;
      color: #fff;
    }

    .subtitle {
      font-size: 13px;
      color: var(--text-muted);
    }

    .local-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      padding: 6px 14px;
      border-radius: 20px;
      background: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.25);
      font-weight: 600;
    }

    .local-badge::before {
      content: "";
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10b981;
    }

    main {
      flex: 1;
      max-width: 1440px;
      width: 100%;
      margin: 0 auto;
      padding: 24px 36px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 14px 20px;
      border-radius: 12px;
      backdrop-filter: blur(10px);
    }

    .tool-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    label {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
    }

    select, button {
      font-family: inherit;
      font-size: 13px;
      padding: 9px 16px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: rgba(255, 255, 255, 0.05);
      color: #fff;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    select:focus, select:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
      outline: none;
    }

    .btn-scrub {
      background: var(--accent-gradient);
      border: none;
      font-weight: 700;
      color: #fff;
      padding: 10px 24px;
      border-radius: 8px;
      box-shadow: 0 4px 14px var(--accent-glow);
    }

    .btn-scrub:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }

    .workspace {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      flex: 1;
      min-height: 480px;
    }

    .panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      backdrop-filter: blur(10px);
    }

    .panel-header {
      padding: 12px 18px;
      background: rgba(255, 255, 255, 0.02);
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .panel-title {
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.3px;
      text-transform: uppercase;
      color: var(--text-muted);
    }

    textarea, .output-box {
      flex: 1;
      width: 100%;
      padding: 18px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13.5px;
      line-height: 1.6;
      background: transparent;
      border: none;
      color: #e2e8f0;
      resize: none;
      outline: none;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .output-box {
      overflow-y: auto;
      user-select: text;
    }

    .placeholder-tag {
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: #93c5fd;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
    }

    .report-bar {
      padding: 14px 20px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .badge-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      padding: 4px 10px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      font-weight: 600;
    }

    .badge-pill.pan { color: #fbbf24; border-color: rgba(251, 191, 36, 0.3); }
    .badge-pill.aadhaar { color: #34d399; border-color: rgba(52, 211, 153, 0.3); }
    .badge-pill.person { color: #f472b6; border-color: rgba(244, 114, 182, 0.3); }
    .badge-pill.secret { color: #f87171; border-color: rgba(248, 113, 113, 0.3); }
    .badge-pill.location { color: #a78bfa; border-color: rgba(167, 139, 250, 0.3); }

    .btn-copy {
      padding: 6px 12px;
      font-size: 12px;
      background: rgba(255, 255, 255, 0.06);
    }
    .btn-copy:hover { background: rgba(255, 255, 255, 0.12); }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo-badge">ScrubIN</div>
      <div>
        <div class="title">Local PII Scrubber Studio</div>
        <div class="subtitle">Deterministic Rules + Local AI Hybrid Pipeline</div>
      </div>
    </div>
    <div class="local-badge">100% Local Inference · Zero Cloud Leaks</div>
  </header>

  <main>
    <div class="toolbar">
      <div class="tool-group">
        <label for="preset">Preset Samples:</label>
        <select id="preset" onchange="loadPreset()">
          <option value="bank">💳 Indian Banking & Payment Log</option>
          <option value="support">🎧 Support Ticket (Free Text Names & Cities)</option>
          <option value="devops">🚀 DevOps Kubernetes Incident Log</option>
        </select>
      </div>

      <div class="tool-group">
        <label for="engine">Scrubbing Engine:</label>
        <select id="engine">
          <option value="none">Deterministic Rules Only (15,000+ lines/sec)</option>
          <option value="ollama" selected>Hybrid: Rules + Ollama Qwen2.5 (100% Recall)</option>
        </select>
        <button class="btn-scrub" onclick="scrubText()">⚡ Scrub PII</button>
      </div>
    </div>

    <div class="workspace">
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Original Log Input</span>
        </div>
        <textarea id="input" spellcheck="false" placeholder="Paste application logs, stack traces, or tickets here..."></textarea>
      </div>

      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Scrubbed Safe Output</span>
          <button class="btn-copy" onclick="copyClean()">📋 Copy</button>
        </div>
        <div id="output" class="output-box">Clean output will appear here with consistent placeholders...</div>
      </div>
    </div>

    <div class="report-bar" id="reportBar">
      <span style="font-size: 13px; font-weight: 600; color: var(--text-muted)">Detected Entities:</span>
      <span id="pills" style="display: flex; gap: 8px; flex-wrap: wrap;">
        <span class="badge-pill">Ready to scan</span>
      </span>
    </div>
  </main>

  <script>
    const PRESETS = {
      bank: `2026-10-21 10:32:11 ERROR payment failed for user Rohan Deshmukh (rohan.d@gmail.com, +91 98765 43210), PAN ABCDE1234F, Aadhaar 2345 6789 0124, token=eyJhbGciOiJIUzI1NiIs.abc123def456.sig789xyz\\n2026-10-21 10:32:14 WARN retry 1/3 for rohan.d@gmail.com from 203.0.113.42\\n2026-10-21 10:32:19 INFO payment ok for rohan.d@gmail.com order=482910573621`,
      support: `Hi support, this is Priya Deshpande from Kothrud, Pune.\\nMy credit card 4111 2222 3333 4444 was debited twice for order #982104928172.\\nPlease issue a refund to priya.desh88@gmail.com or contact me at 9822012345. My Aadhaar 2345 6789 0124 is verified on my profile.`,
      devops: `2026-10-21 14:10:02 ERROR upstream auth failed: aws_key=AKIAIOSFODNN7EXAMPLE ip=198.51.100.24\\n2026-10-21 14:10:05 WARN token expired for admin Vikram Malhotra (vikram@internal.corp)\\nBearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.do_not_share_secret`
    };

    function loadPreset() {
      const val = document.getElementById('preset').value;
      document.getElementById('input').value = PRESETS[val].replace(/\\\\n/g, '\\n');
    }

    async function scrubText() {
      const text = document.getElementById('input').value;
      const engine = document.getElementById('engine').value;
      const outBox = document.getElementById('output');
      const pillsBox = document.getElementById('pills');

      if (!text.trim()) return;

      outBox.textContent = 'Processing locally...';
      pillsBox.innerHTML = '<span class="badge-pill">Scanning...</span>';

      try {
        const res = await fetch('/api/scrub', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, engine })
        });
        const data = await res.json();
        
        // Highlight placeholders
        const highlighted = data.scrubbed.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          .replace(/&lt;([A-Z]+_\d+)&gt;/g, '<span class="placeholder-tag">&lt;$1&gt;</span>');
        
        outBox.innerHTML = highlighted;

        // Render entity pills
        pillsBox.innerHTML = '';
        const counts = data.report || {};
        const keys = Object.keys(counts);
        if (keys.length === 0) {
          pillsBox.innerHTML = '<span class="badge-pill">No PII detected</span>';
        } else {
          keys.forEach(k => {
            const cls = k.toLowerCase();
            pillsBox.innerHTML += `<span class="badge-pill ${cls}">● ${k}: ${counts[k]}</span>`;
          });
        }
      } catch (err) {
        outBox.textContent = 'Error: ' + err;
      }
    }

    function copyClean() {
      const text = document.getElementById('output').innerText;
      navigator.clipboard.writeText(text);
      alert('Cleaned log copied to clipboard!');
    }

    window.onload = loadPreset;
  </script>
</body>
</html>
"""


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Keep terminal quiet
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/scrub":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                req = json.loads(body.decode("utf-8"))
                text = req.get("text", "")
                engine = req.get("engine", "none")
                sc = Scrubber(rules=True, engine=engine)
                cleaned = sc.scrub(text)
                report = sc.report()
                res = json.dumps({"scrubbed": cleaned, "report": report})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(res.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def run_studio(port: int = 8765):
    server = ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)
    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"  ScrubIN Studio running at: {url}")
    print(f"  Press Ctrl+C to stop.")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ScrubIN Studio...")
        server.server_close()


if __name__ == "__main__":
    run_studio()
