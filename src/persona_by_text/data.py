from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple


def read_dataset_from_directory(root_dir: str | os.PathLike[str]) -> Tuple[List[str], List[str]]:
    """
    Load a dataset organized as:
      root_dir/
        author_a/*.txt
        author_b/*.txt
    Returns (texts, labels).
    """
    root_path = Path(root_dir)
    if not root_path.exists() or not root_path.is_dir():
        raise FileNotFoundError(f"Dataset directory not found: {root_dir}")

    texts: List[str] = []
    labels: List[str] = []

    for author_dir in sorted(p for p in root_path.iterdir() if p.is_dir()):
        author_label = author_dir.name
        for text_file in sorted(author_dir.rglob("*.txt")):
            try:
                text = _read_text_file(text_file)
            except Exception:
                # Skip unreadable files
                continue
            if not text.strip():
                continue
            texts.append(text)
            labels.append(author_label)

    if not texts:
        raise ValueError(
            "No .txt files were found. Expected structure: root/author/*.txt"
        )

    return texts, labels


def _read_text_file(path: os.PathLike[str] | str) -> str:
    """Robust text read with UTF-8 first, fallback to latin-1."""
    file_path = Path(path)
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1", errors="ignore")
