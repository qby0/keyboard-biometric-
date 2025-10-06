from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class KeystrokeRecord:
    # One typed sample (e.g., a sentence), with key events in chronological order
    # Each event: {"key": str, "t": float, "type": "down"|"up"}
    events: List[Dict]
    label: str


class KeystrokeFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract keystroke dynamics features (hold times, latencies)."""

    def fit(self, X: Sequence[List[Dict]], y: Optional[Sequence[str]] = None):
        return self

    def transform(self, X: Sequence[List[Dict]]):
        features: List[List[float]] = []
        for events in X:
            features.append(self._extract_from_events(events))
        return np.array(features, dtype=float)

    @staticmethod
    def _extract_from_events(events: List[Dict]) -> List[float]:
        # Data structures for press/release times by key
        down_times: Dict[str, List[float]] = {}
        up_times: Dict[str, List[float]] = {}
        inter_key_latencies: List[float] = []

        last_down_time: Optional[float] = None

        for e in events:
            et = e.get("type")
            key = str(e.get("key"))
            t = float(e.get("t"))
            if et == "down":
                down_times.setdefault(key, []).append(t)
                if last_down_time is not None:
                    inter_key_latencies.append(t - last_down_time)
                last_down_time = t
            elif et == "up":
                up_times.setdefault(key, []).append(t)

        # Hold times per key instance where possible
        hold_times: List[float] = []
        for key, downs in down_times.items():
            ups = up_times.get(key, [])
            n = min(len(downs), len(ups))
            for i in range(n):
                hold_times.append(ups[i] - downs[i])

        # Aggregate statistics
        def _stats(values: List[float]) -> List[float]:
            if not values:
                return [0.0, 0.0, 0.0, 0.0]
            arr = np.array(values, dtype=float)
            return [
                float(np.mean(arr)),
                float(np.std(arr)),
                float(np.median(arr)),
                float(np.percentile(arr, 90)),
            ]

        feature_vector: List[float] = []
        feature_vector += _stats(hold_times)
        feature_vector += _stats(inter_key_latencies)
        # Length-based normalization signals
        feature_vector.append(float(len(events)))
        feature_vector.append(float(len(hold_times)))
        feature_vector.append(float(len(inter_key_latencies)))
        return feature_vector


def create_keystroke_pipeline(random_state: int = 42) -> Pipeline:
    extractor = KeystrokeFeatureExtractor()
    scaler = StandardScaler()
    clf = LogisticRegression(
        solver="lbfgs",
        max_iter=1000,
        multi_class="auto",
        random_state=random_state,
    )
    return Pipeline([
        ("feat", extractor),
        ("scaler", scaler),
        ("clf", clf),
    ])


def fit_keystroke_and_evaluate(
    sequences: Sequence[List[Dict]],
    labels: Sequence[str],
    *,
    validation_split: float = 0.2,
    random_state: int = 42,
):
    x_train, x_val, y_train, y_val = train_test_split(
        list(sequences), list(labels), test_size=validation_split, random_state=random_state, stratify=list(labels)
    )
    pipeline = create_keystroke_pipeline(random_state=random_state)
    pipeline.fit(x_train, y_train)
    preds = pipeline.predict(x_val)
    acc = accuracy_score(y_val, preds)
    macro = f1_score(y_val, preds, average="macro")
    report = classification_report(y_val, preds)
    return {
        "model": pipeline,
        "accuracy": acc,
        "macro_f1": macro,
        "report": report,
    }
