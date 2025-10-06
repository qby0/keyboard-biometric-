from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .data import read_dataset_from_directory
from .ks_data import read_keystroke_dataset
from .model import (
    create_pipeline,
    fit_and_evaluate,
    load_model,
    predict_texts,
    save_model,
)
from .keystroke import create_keystroke_pipeline, fit_keystroke_and_evaluate


def _positive_float(value: str) -> float:
    try:
        f = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Must be a float")
    if not 0.0 < f < 1.0:
        raise argparse.ArgumentTypeError("Must be between 0 and 1 (exclusive)")
    return f


def cmd_train(args: argparse.Namespace) -> int:
    texts, labels = read_dataset_from_directory(args.data)
    result = fit_and_evaluate(
        texts,
        labels,
        validation_split=args.val_split,
        random_state=args.random_state,
    )

    if args.model_out:
        model_path = Path(args.model_out)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        save_model(result.model, str(model_path))

    print("Accuracy:", f"{result.accuracy:.4f}" if result.accuracy is not None else "n/a")
    print("Macro-F1:", f"{result.macro_f1:.4f}" if result.macro_f1 is not None else "n/a")
    if result.report:
        print("\nClassification report:\n")
        print(result.report)
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    texts, labels = read_dataset_from_directory(args.data)

    preds, _ = predict_texts(model, texts)

    # Lazy import to keep CLI fast
    from sklearn.metrics import accuracy_score, classification_report, f1_score

    acc = accuracy_score(labels, preds)
    macro = f1_score(labels, preds, average="macro")
    print("Accuracy:", f"{acc:.4f}")
    print("Macro-F1:", f"{macro:.4f}")
    print("\nClassification report:\n")
    print(classification_report(labels, preds))
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    model = load_model(args.model)

    if args.file and args.text:
        print("Provide either --file or --text, not both", file=sys.stderr)
        return 2

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("Provide --file or --text", file=sys.stderr)
        return 2

    labels, proba = predict_texts(model, [text])
    output = {"label": labels[0]}
    if proba is not None:
        # Return probabilities per class
        clf = model.named_steps.get("clf")
        classes = list(getattr(clf, "classes_", []))
        output["probabilities"] = [
            {"label": str(classes[i]), "p": float(proba[0][i])}
            for i in range(len(classes))
        ]
        output["probabilities"].sort(key=lambda x: x["p"], reverse=True)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="persona-text",
        description=(
            "Authorship identification (stylometry) using scikit-learn.\n"
            "Data layout: data_dir/{author}/*.txt"
        ),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser("train", help="Train on directory and save model")
    p_train.add_argument("--data", required=True, help="Training data directory")
    p_train.add_argument(
        "--val-split",
        type=_positive_float,
        default=0.2,
        help="Validation split fraction (0-1)",
    )
    p_train.add_argument(
        "--model-out",
        required=True,
        help="Path to save the trained model (e.g., model.joblib)",
    )
    p_train.add_argument("--random-state", type=int, default=42)
    p_train.set_defaults(func=cmd_train)

    p_eval = sub.add_parser("evaluate", help="Evaluate a saved model on a dataset")
    p_eval.add_argument("--model", required=True, help="Path to model .joblib")
    p_eval.add_argument("--data", required=True, help="Evaluation data directory")
    p_eval.set_defaults(func=cmd_evaluate)

    p_pred = sub.add_parser("predict", help="Predict author for a single text")
    p_pred.add_argument("--model", required=True, help="Path to model .joblib")
    group = p_pred.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to text file to classify")
    group.add_argument("--text", help="Raw text to classify")
    p_pred.set_defaults(func=cmd_predict)

    # Keystroke subcommands
    p_ks_train = sub.add_parser(
        "ks-train", help="Train keystroke dynamics model on JSON datasets"
    )
    p_ks_train.add_argument("--data", required=True, help="Dataset root (user/*.json)")
    p_ks_train.add_argument(
        "--val-split", type=_positive_float, default=0.2, help="Validation split"
    )
    p_ks_train.add_argument(
        "--model-out", required=True, help="Path to save model (e.g., ks_model.joblib)"
    )
    p_ks_train.add_argument("--random-state", type=int, default=42)
    p_ks_train.set_defaults(func=cmd_ks_train)

    p_ks_eval = sub.add_parser(
        "ks-evaluate", help="Evaluate a keystroke model on a dataset"
    )
    p_ks_eval.add_argument("--model", required=True, help="Path to model .joblib")
    p_ks_eval.add_argument("--data", required=True, help="Dataset root (user/*.json)")
    p_ks_eval.set_defaults(func=cmd_ks_evaluate)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


# -------------- Keystroke command implementations --------------

def cmd_ks_train(args: argparse.Namespace) -> int:
    sequences, labels = read_keystroke_dataset(args.data)
    result = fit_keystroke_and_evaluate(
        sequences,
        labels,
        validation_split=args.val_split,
        random_state=args.random_state,
    )
    if args.model_out:
        model_path = Path(args.model_out)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        from .model import save_model  # reuse joblib helper

        save_model(result["model"], str(model_path))

    print("Accuracy:", f"{result['accuracy']:.4f}")
    print("Macro-F1:", f"{result['macro_f1']:.4f}")
    print("\nClassification report:\n")
    print(result["report"])
    return 0


def cmd_ks_evaluate(args: argparse.Namespace) -> int:
    from .model import load_model
    model = load_model(args.model)
    sequences, labels = read_keystroke_dataset(args.data)
    preds = model.predict(sequences)

    from sklearn.metrics import accuracy_score, classification_report, f1_score

    acc = accuracy_score(labels, preds)
    macro = f1_score(labels, preds, average="macro")
    print("Accuracy:", f"{acc:.4f}")
    print("Macro-F1:", f"{macro:.4f}")
    print("\nClassification report:\n")
    print(classification_report(labels, preds))
    return 0
