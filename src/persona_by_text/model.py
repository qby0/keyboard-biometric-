from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Sequence, Optional

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline


DEFAULT_RANDOM_STATE = 42


@dataclass
class TrainResult:
    model: Pipeline
    accuracy: Optional[float]
    macro_f1: Optional[float]
    report: Optional[str]


def create_pipeline(random_state: int = DEFAULT_RANDOM_STATE) -> Pipeline:
    """Create a stylometry pipeline combining char and word n-grams."""
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=3,
        max_features=300_000,
        lowercase=True,
    )

    word_vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=2,
        max_features=200_000,
        token_pattern=r"(?u)\\b\\w+\\b",
        lowercase=True,
    )

    features = FeatureUnion([
        ("char", char_vectorizer),
        ("word", word_vectorizer),
    ])

    classifier = LogisticRegression(
        solver="saga",
        penalty="l2",
        max_iter=1500,
        n_jobs=-1,
        random_state=random_state,
    )

    pipeline = Pipeline([
        ("features", features),
        ("clf", classifier),
    ])
    return pipeline


def fit_and_evaluate(
    texts: Sequence[str],
    labels: Sequence[str],
    *,
    validation_split: float = 0.2,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> TrainResult:
    """
    Fit the pipeline and evaluate on a validation split.
    Returns TrainResult with metrics; metrics are None if no validation_split.
    """
    if not 0.0 < validation_split < 1.0:
        raise ValueError("validation_split must be between 0 and 1")

    x_train, x_val, y_train, y_val = train_test_split(
        list(texts),
        list(labels),
        test_size=validation_split,
        random_state=random_state,
        stratify=list(labels),
    )

    pipeline = create_pipeline(random_state=random_state)
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_val)
    acc = accuracy_score(y_val, y_pred)
    macro = f1_score(y_val, y_pred, average="macro")
    report = classification_report(y_val, y_pred)

    return TrainResult(model=pipeline, accuracy=acc, macro_f1=macro, report=report)


def save_model(model: Pipeline, path: str) -> None:
    joblib.dump(model, path)


def load_model(path: str) -> Pipeline:
    return joblib.load(path)


def predict_texts(model: Pipeline, texts: Sequence[str]) -> Tuple[List[str], Optional[List[List[float]]]]:
    """
    Predict author labels; if the classifier supports predict_proba, also return probabilities.
    Returns (predicted_labels, probabilities_or_None).
    """
    preds = model.predict(list(texts))
    proba = None
    clf = model.named_steps.get("clf")
    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba(model.named_steps["features"].transform(list(texts))).tolist()
    return list(preds), proba
