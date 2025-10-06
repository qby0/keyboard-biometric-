from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template_string, request

try:
    # Optional import; only used if prediction is enabled
    from .model import load_model
except Exception:  # pragma: no cover - optional path
    load_model = None  # type: ignore


def create_app(save_root: str | os.PathLike[str] = "./keystroke_data") -> Flask:
    app = Flask(__name__)
    save_root_path = Path(save_root)
    save_root_path.mkdir(parents=True, exist_ok=True)

    # Lazy model holder for prediction (optional)
    app.config["KS_MODEL_PATH"] = os.getenv("KS_MODEL_PATH")
    app.config["KS_MODEL"] = None

    def _get_model():
        model = app.config.get("KS_MODEL")
        if model is not None:
            return model
        model_path = app.config.get("KS_MODEL_PATH")
        if not model_path or load_model is None:
            return None
        try:
            model = load_model(model_path)
            app.config["KS_MODEL"] = model
            return model
        except Exception:
            return None

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

    @app.post("/api/predict")
    def predict():
        """Predict user label from keystroke events. Requires KS_MODEL_PATH env var."""
        model = _get_model()
        if model is None:
            return jsonify({"error": "Prediction model not loaded. Set KS_MODEL_PATH env var."}), 503

        payload: Dict[str, Any] = request.get_json(force=True)
        events = payload.get("events", [])
        if not isinstance(events, list) or not events:
            return jsonify({"error": "events list required"}), 400

        try:
            labels = model.predict([events])
            result = {"label": str(labels[0])}
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba([events])[0]
                classes = getattr(model.named_steps.get("clf"), "classes_", [])
                pairs = [(str(classes[i]), float(proba[i])) for i in range(len(classes))]
                pairs.sort(key=lambda x: x[1], reverse=True)
                # Return top-5 similar users
                result["probabilities"] = [
                    {"label": lbl, "p": p} for lbl, p in pairs[:5]
                ]
            return jsonify(result)
        except Exception as e:  # minimal error handling
            return jsonify({"error": "prediction failed"}), 500

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
  <p class="help">Печатайте в поле ниже — время будет записываться. Клавиши на клавиатуре подсвечиваются при нажатии. Кнопка Predict покажет топ похожих пользователей.</p>

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
    <div id="kbd-container">
      <!-- Simple inline SVG keyboard -->
      <svg id="keyboard" viewBox="0 0 800 260" width="100%" style="max-width:800px;border:1px solid #ddd;border-radius:8px;">
        <style>
          .key rect { fill: #f6f7f9; stroke: #999; rx: 6; ry: 6; }
          .key.active rect { fill: #9ad0f5; }
          .key text { font-family: sans-serif; font-size: 14px; fill: #222; user-select: none; }
        </style>
        <!-- Row 1: digits -->
        <!-- positions -->
        <g class="key" id="KEY-1"><rect x="20" y="20" width="60" height="50"/><text x="50" y="50" text-anchor="middle">1</text></g>
        <g class="key" id="KEY-2"><rect x="84" y="20" width="60" height="50"/><text x="114" y="50" text-anchor="middle">2</text></g>
        <g class="key" id="KEY-3"><rect x="148" y="20" width="60" height="50"/><text x="178" y="50" text-anchor="middle">3</text></g>
        <g class="key" id="KEY-4"><rect x="212" y="20" width="60" height="50"/><text x="242" y="50" text-anchor="middle">4</text></g>
        <g class="key" id="KEY-5"><rect x="276" y="20" width="60" height="50"/><text x="306" y="50" text-anchor="middle">5</text></g>
        <g class="key" id="KEY-6"><rect x="340" y="20" width="60" height="50"/><text x="370" y="50" text-anchor="middle">6</text></g>
        <g class="key" id="KEY-7"><rect x="404" y="20" width="60" height="50"/><text x="434" y="50" text-anchor="middle">7</text></g>
        <g class="key" id="KEY-8"><rect x="468" y="20" width="60" height="50"/><text x="498" y="50" text-anchor="middle">8</text></g>
        <g class="key" id="KEY-9"><rect x="532" y="20" width="60" height="50"/><text x="562" y="50" text-anchor="middle">9</text></g>
        <g class="key" id="KEY-0"><rect x="596" y="20" width="60" height="50"/><text x="626" y="50" text-anchor="middle">0</text></g>
        <!-- Row 2: QWERTY -->
        <g class="key" id="KEY-Q"><rect x="50" y="78" width="60" height="50"/><text x="80" y="108" text-anchor="middle">Q</text></g>
        <g class="key" id="KEY-W"><rect x="114" y="78" width="60" height="50"/><text x="144" y="108" text-anchor="middle">W</text></g>
        <g class="key" id="KEY-E"><rect x="178" y="78" width="60" height="50"/><text x="208" y="108" text-anchor="middle">E</text></g>
        <g class="key" id="KEY-R"><rect x="242" y="78" width="60" height="50"/><text x="272" y="108" text-anchor="middle">R</text></g>
        <g class="key" id="KEY-T"><rect x="306" y="78" width="60" height="50"/><text x="336" y="108" text-anchor="middle">T</text></g>
        <g class="key" id="KEY-Y"><rect x="370" y="78" width="60" height="50"/><text x="400" y="108" text-anchor="middle">Y</text></g>
        <g class="key" id="KEY-U"><rect x="434" y="78" width="60" height="50"/><text x="464" y="108" text-anchor="middle">U</text></g>
        <g class="key" id="KEY-I"><rect x="498" y="78" width="60" height="50"/><text x="528" y="108" text-anchor="middle">I</text></g>
        <g class="key" id="KEY-O"><rect x="562" y="78" width="60" height="50"/><text x="592" y="108" text-anchor="middle">O</text></g>
        <g class="key" id="KEY-P"><rect x="626" y="78" width="60" height="50"/><text x="656" y="108" text-anchor="middle">P</text></g>
        <!-- Row 3: ASDF -->
        <g class="key" id="KEY-A"><rect x="70" y="136" width="60" height="50"/><text x="100" y="166" text-anchor="middle">A</text></g>
        <g class="key" id="KEY-S"><rect x="134" y="136" width="60" height="50"/><text x="164" y="166" text-anchor="middle">S</text></g>
        <g class="key" id="KEY-D"><rect x="198" y="136" width="60" height="50"/><text x="228" y="166" text-anchor="middle">D</text></g>
        <g class="key" id="KEY-F"><rect x="262" y="136" width="60" height="50"/><text x="292" y="166" text-anchor="middle">F</text></g>
        <g class="key" id="KEY-G"><rect x="326" y="136" width="60" height="50"/><text x="356" y="166" text-anchor="middle">G</text></g>
        <g class="key" id="KEY-H"><rect x="390" y="136" width="60" height="50"/><text x="420" y="166" text-anchor="middle">H</text></g>
        <g class="key" id="KEY-J"><rect x="454" y="136" width="60" height="50"/><text x="484" y="166" text-anchor="middle">J</text></g>
        <g class="key" id="KEY-K"><rect x="518" y="136" width="60" height="50"/><text x="548" y="166" text-anchor="middle">K</text></g>
        <g class="key" id="KEY-L"><rect x="582" y="136" width="60" height="50"/><text x="612" y="166" text-anchor="middle">L</text></g>
        <!-- Row 4: ZXCV -->
        <g class="key" id="KEY-Z"><rect x="90" y="194" width="60" height="50"/><text x="120" y="224" text-anchor="middle">Z</text></g>
        <g class="key" id="KEY-X"><rect x="154" y="194" width="60" height="50"/><text x="184" y="224" text-anchor="middle">X</text></g>
        <g class="key" id="KEY-C"><rect x="218" y="194" width="60" height="50"/><text x="248" y="224" text-anchor="middle">C</text></g>
        <g class="key" id="KEY-V"><rect x="282" y="194" width="60" height="50"/><text x="312" y="224" text-anchor="middle">V</text></g>
        <g class="key" id="KEY-B"><rect x="346" y="194" width="60" height="50"/><text x="376" y="224" text-anchor="middle">B</text></g>
        <g class="key" id="KEY-N"><rect x="410" y="194" width="60" height="50"/><text x="440" y="224" text-anchor="middle">N</text></g>
        <g class="key" id="KEY-M"><rect x="474" y="194" width="60" height="50"/><text x="504" y="224" text-anchor="middle">M</text></g>
        <!-- Spacebar -->
        <g class="key" id="KEY-SPACE"><rect x="200" y="252" width="400" height="40"/><text x="400" y="278" text-anchor="middle">SPACE</text></g>
      </svg>
    </div>
  </div>

  <div class="row">
    <button id="submit">Submit sample</button>
    <button id="predict">Predict</button>
    <span id="status"></span>
  </div>

  <div class="row">
    <label>Top похожих пользователей</label>
    <ul id="top-similar"></ul>
  </div>

  <script>
  const typing = document.getElementById('typing');
  const status = document.getElementById('status');
  const user = document.getElementById('user');
  const phrase = document.getElementById('phrase');
  const topList = document.getElementById('top-similar');

  let events = [];
  let t0 = null;

  function now() { return performance.now(); }

  function keyIdFromEventKey(k) {
    if (!k) return null;
    if (k === ' ') return 'KEY-SPACE';
    const upper = k.length === 1 ? k.toUpperCase() : k.toUpperCase();
    if (/^[A-Z]$/.test(upper)) return 'KEY-' + upper;
    if (/^[0-9]$/.test(k)) return 'KEY-' + k;
    return null;
  }

  function setKeyActive(kid, active) {
    if (!kid) return;
    const el = document.getElementById(kid);
    if (!el) return;
    if (active) el.classList.add('active'); else el.classList.remove('active');
  }

  typing.addEventListener('keydown', (e) => {
    if (t0 === null) t0 = now();
    events.push({ key: e.key, type: 'down', t: now() - t0 });
    setKeyActive(keyIdFromEventKey(e.key), true);
  });
  typing.addEventListener('keyup', (e) => {
    if (t0 === null) t0 = now();
    events.push({ key: e.key, type: 'up', t: now() - t0 });
    setKeyActive(keyIdFromEventKey(e.key), false);
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
        topList.innerHTML = '';
      } else {
        status.textContent = 'Error: ' + (data.error || 'unknown'); status.className='err';
      }
    } catch (err) {
      status.textContent = 'Network error'; status.className='err';
    }
  });

  document.getElementById('predict').addEventListener('click', async () => {
    status.textContent = 'Predicting...'; status.className='';
    try {
      const resp = await fetch('/api/predict', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events })
      });
      const data = await resp.json();
      if (resp.ok) {
        status.textContent = 'Predicted: ' + data.label; status.className='ok';
        topList.innerHTML = '';
        if (Array.isArray(data.probabilities)) {
          for (const p of data.probabilities) {
            const li = document.createElement('li');
            li.textContent = `${p.label}: ${p.p.toFixed(2)}`;
            topList.appendChild(li);
          }
        }
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
