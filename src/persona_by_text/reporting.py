from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix

from .data import read_dataset_from_directory
from .ks_data import read_keystroke_dataset
from .model import load_model


def _ensure_dir(path: str | os.PathLike[str]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_text_report(model_path: str, data_dir: str, out_dir: str) -> None:
    out = _ensure_dir(out_dir)
    model = load_model(model_path)
    texts, labels = read_dataset_from_directory(data_dir)
    preds = model.predict(texts)

    report = classification_report(labels, preds, output_dict=True)
    _save_json(report, out / "classification_report.json")

    cm = confusion_matrix(labels, preds, labels=sorted(set(labels)))
    labels_sorted = sorted(set(labels))
    np.savetxt(out / "confusion_matrix.csv", cm, fmt="%d", delimiter=",")

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels_sorted)
    try:
        import matplotlib.pyplot as plt  # type: ignore

        fig, ax = plt.subplots(figsize=(6, 6))
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        fig.tight_layout()
        fig.savefig(out / "confusion_matrix.png")
        plt.close(fig)
    except Exception:
        # matplotlib might be missing; fallback to JSON only
        pass


def generate_keystroke_report(model_path: str, data_dir: str, out_dir: str) -> None:
    out = _ensure_dir(out_dir)
    model = load_model(model_path)
    sequences, labels = read_keystroke_dataset(data_dir)
    preds = model.predict(sequences)

    report = classification_report(labels, preds, output_dict=True)
    _save_json(report, out / "classification_report.json")

    cm = confusion_matrix(labels, preds, labels=sorted(set(labels)))
    labels_sorted = sorted(set(labels))
    np.savetxt(out / "confusion_matrix.csv", cm, fmt="%d", delimiter=",")

    try:
        import matplotlib.pyplot as plt  # type: ignore
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels_sorted)
        fig, ax = plt.subplots(figsize=(6, 6))
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        fig.tight_layout()
        fig.savefig(out / "confusion_matrix.png")
        plt.close(fig)
    except Exception:
        pass
