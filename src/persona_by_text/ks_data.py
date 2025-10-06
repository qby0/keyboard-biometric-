from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


def read_keystroke_dataset(root_dir: str) -> Tuple[List[List[Dict]], List[str]]:
    """
    Load dataset structured as:
      root_dir/
        user_a/*.json
        user_b/*.json
    Each JSON is a list of events: {"key": <str>, "type": "down"|"up", "t": <float_ms>}
    Returns (sequences, labels)
    """
    root = Path(root_dir)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Dataset directory not found: {root_dir}")

    sequences: List[List[Dict]] = []
    labels: List[str] = []

    for user_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        label = user_dir.name
        for json_file in sorted(user_dir.rglob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    sequences.append(data)
                    labels.append(label)
            except Exception:
                continue

    if not sequences:
        raise ValueError("No JSON keystroke files found. Expected root/user/*.json")

    return sequences, labels
