"""
train.py -- Train a phishing email classifier and save it to disk.

Pipeline: TF-IDF vectorizer -> Logistic Regression
Outputs:  accuracy, precision, recall, F1 to stdout
Saves:    phishing_model.joblib (the fitted pipeline)

Run:
    python train.py
"""

import argparse
from pathlib import Path
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

from generate_data import generate_dataset

MODEL_PATH = "phishing_model.joblib"
TEST_SIZE = 0.2
RANDOM_STATE = 42
DEFAULT_DATASET_PATHS = ["Datasets"]


def parse_args():
    parser = argparse.ArgumentParser(description="Train a phishing email classifier.")
    parser.add_argument(
        "--dataset-paths",
        nargs="+",
        default=None,
        help="Optional local dataset file paths or directories to use instead of synthetic data.",
    )
    parser.add_argument(
        "--model-path",
        default=MODEL_PATH,
        help="Output path for the saved trained model.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=TEST_SIZE,
        help="Fraction of data reserved for evaluation.",
    )
    return parser.parse_args()


def build_pipeline() -> Pipeline:
    """Return an untrained sklearn pipeline: TF-IDF + Logistic Regression."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),  # unigrams and bigrams
            max_features=5000,
            sublinear_tf=True,   # apply log(1 + tf) scaling
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE,
            C=1.0,
        )),
    ])


def print_metrics(y_true, y_pred) -> None:
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall   : {rec:.4f}")
    print(f"  F1       : {f1:.4f}")
    print()
    print("Full classification report (phishing=1, ham=0):")
    print(classification_report(y_true, y_pred, target_names=["ham", "phishing"]))


def main():
    args = parse_args()

    print("Loading dataset...")
    if not args.dataset_paths:
        args.dataset_paths = list(DEFAULT_DATASET_PATHS)
        enhancements_path = Path("enhancements")
        if enhancements_path.exists():
            args.dataset_paths.append("enhancements")
    print(f"Using dataset paths: {args.dataset_paths}")

    df = generate_dataset(dataset_paths=args.dataset_paths)
    X = df["text"].tolist()
    y = df["label"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples\n")

    print("Training pipeline (TF-IDF + Logistic Regression)...")
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    print("Evaluating on test set:")
    y_pred = pipeline.predict(X_test)
    print_metrics(y_test, y_pred)

    joblib.dump(pipeline, args.model_path)
    print(f"Model saved to: {args.model_path}")


if __name__ == "__main__":
    main()
