from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template_string, request


def create_app(save_root: str | os.PathLike[str] = "./keystroke_data") -> Flask:
    app = Flask(__name__)
    save_root_path = Path(save_root)
    save_root_path.mkdir(parents=True, exist_ok=True)

    @app.get("/")
    def index():
        return render_template_string(INDEX_HTML)

    @app.post("/api/submit")
    def submit():
        payload: Dict[str, Any] = request.get_json(force=True)
        user_id = str(payload.get("user_id", "unknown")).strip()
        phrase = str(payload.get("phrase", "")).strip()
        events = payload.get("events", [])
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        if not isinstance(events, list) or not events:
            return jsonify({"error": "events list required"}), 400

        user_dir = save_root_path / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        fname = f"{ts}.json"
        out = {
            "user_id": user_id,
            "phrase": phrase,
            "events": events,
        }
        (user_dir / fname).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        return jsonify({"ok": True, "file": str(user_dir / fname)})

    return app


def main():
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


INDEX_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Keystroke Capture</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: sans-serif; margin: 2rem; }
    .row { margin-bottom: 1rem; }
    input, textarea { width: 100%; padding: 0.6rem; }
    button { padding: 0.6rem 1rem; font-size: 1rem; }
    .help { color: #555; font-size: 0.9rem; }
    .ok { color: #0a0; }
    .err { color: #a00; }
  </style>
</head>
<body>
  <h1>Keystroke Capture</h1>
  <p class="help">Type the phrase in the box below. Timing will be recorded.</p>

  <div class="row">
    <label>User ID</label>
    <input id="user" placeholder="e.g., user123" />
  </div>

  <div class="row">
    <label>Prompt phrase (optional)</label>
    <input id="phrase" placeholder="e.g., The quick brown fox..." />
  </div>

  <div class="row">
    <label>Type here</label>
    <textarea id="typing" rows="6" placeholder="Start typing..." ></textarea>
  </div>

  <div class="row">
    <button id="submit">Submit sample</button>
    <span id="status"></span>
  </div>

  <script>
  const typing = document.getElementById('typing');
  const status = document.getElementById('status');
  const user = document.getElementById('user');
  const phrase = document.getElementById('phrase');

  let events = [];
  let t0 = null;

  function now() { return performance.now(); }

  typing.addEventListener('keydown', (e) => {
    if (t0 === null) t0 = now();
    events.push({ key: e.key, type: 'down', t: now() - t0 });
  });
  typing.addEventListener('keyup', (e) => {
    if (t0 === null) t0 = now();
    events.push({ key: e.key, type: 'up', t: now() - t0 });
  });

  document.getElementById('submit').addEventListener('click', async () => {
    status.textContent = 'Submitting...'; status.className='';
    try {
      const resp = await fetch('/api/submit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.value, phrase: phrase.value, events })
      });
      const data = await resp.json();
      if (resp.ok) {
        status.textContent = 'Saved: ' + data.file; status.className='ok';
        events = []; t0 = null; typing.value = '';
      } else {
        status.textContent = 'Error: ' + (data.error || 'unknown'); status.className='err';
      }
    } catch (err) {
      status.textContent = 'Network error'; status.className='err';
    }
  });
  </script>
</body>
</html>
"""
