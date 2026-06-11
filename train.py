"""
train.py -- Train a phishing email classifier and save it to disk.

Pipeline: TF-IDF vectorizer -> Logistic Regression
Outputs:  accuracy, precision, recall, F1 to stdout
Saves:    phishing_model.joblib (the fitted pipeline)

Run:
    python train.py
"""

import argparse
import joblib
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

from generate_data import generate_dataset
from scripts.model_wrappers import WrappedModel

MODEL_PATH = "phishing_model.joblib"
TEST_SIZE = 0.2
RANDOM_STATE = 42
ENHANCEMENT_MULTIPLIER = 300


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
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Force streaming training (HashingVectorizer + SGD) instead of TF-IDF pipeline.",
    )
    parser.add_argument(
        "--enhancement-multiplier",
        type=int,
        default=ENHANCEMENT_MULTIPLIER,
        help=(
            "Default number of total times enhancement examples should influence training. "
            "Used for both classes unless a class-specific multiplier is provided. "
            "Use 1 to disable oversampling."
        ),
    )
    parser.add_argument(
        "--phishing-enhancement-multiplier",
        type=int,
        default=None,
        help="Override multiplier for phishing enhancement examples (label 1).",
    )
    parser.add_argument(
        "--false-positive-enhancement-multiplier",
        type=int,
        default=None,
        help="Override multiplier for false-positive/ham enhancement examples (label 0).",
    )
    return parser.parse_args()


def find_enhancement_paths(dataset_paths: list[str] | None) -> list[str]:
    """Return enhancement directories that are included by the requested datasets."""
    if not dataset_paths:
        dataset_paths = ["Datasets"]

    found = []
    seen = set()
    for raw_path in dataset_paths:
        path = Path(raw_path)
        candidates = []
        if path.name.lower() == "enhancements":
            candidates.append(path)
        candidates.append(path / "enhancements")

        for candidate in candidates:
            resolved = candidate.resolve()
            if candidate.exists() and resolved not in seen:
                found.append(str(candidate))
                seen.add(resolved)

    return found


def load_enhancement_rows(dataset_paths: list[str] | None) -> pd.DataFrame:
    """Load enhancement examples separately so they can be weighted in training."""
    enhancement_paths = find_enhancement_paths(dataset_paths)
    if not enhancement_paths:
        return pd.DataFrame({"text": [], "label": []})

    return generate_dataset(dataset_paths=enhancement_paths)


def apply_enhancement_oversampling(
    X_train: list[str],
    y_train: list[int],
    enhancement_df: pd.DataFrame,
    default_multiplier: int,
    phishing_multiplier: int | None = None,
    false_positive_multiplier: int | None = None,
) -> tuple[list[str], list[int]]:
    """Append enhancement examples to the training split without leaking into test."""
    if enhancement_df.empty:
        return X_train, y_train

    phishing_multiplier = (
        default_multiplier if phishing_multiplier is None else phishing_multiplier
    )
    false_positive_multiplier = (
        default_multiplier if false_positive_multiplier is None else false_positive_multiplier
    )

    extra_X = []
    extra_y = []
    multiplier_by_label = {
        1: phishing_multiplier,
        0: false_positive_multiplier,
    }

    for label, multiplier in multiplier_by_label.items():
        if multiplier <= 1:
            continue
        label_rows = enhancement_df[enhancement_df["label"] == label]
        if label_rows.empty:
            continue
        extra_repeats = multiplier - 1
        extra_X.extend(label_rows["text"].tolist() * extra_repeats)
        extra_y.extend(label_rows["label"].astype(int).tolist() * extra_repeats)

        label_name = "phishing" if label == 1 else "false_positive"
        print(
            f"Oversampling {label_name} enhancements: {len(label_rows)} rows "
            f"x{multiplier} ({len(label_rows) * extra_repeats} extra training rows)"
        )

    if not extra_X:
        return X_train, y_train

    print(
        f"Total enhancement oversampling: {len(enhancement_df)} rows "
        f"({len(extra_X)} extra training rows)"
    )
    return X_train + extra_X, y_train + extra_y


def build_pipeline() -> Pipeline:
    """Return an untrained sklearn pipeline: TF-IDF + Logistic Regression."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),  # unigrams and bigrams
            max_features=5000,
            sublinear_tf=True,   # apply log(1 + tf) scaling
        )),
        ("clf", LogisticRegression(
            solver="saga",
            max_iter=1000,
            random_state=RANDOM_STATE,
            C=1.0,
        )),
    ])


def streaming_train(df: "pd.DataFrame", enhancement_df: "pd.DataFrame", args) -> tuple:
    """Train using a streaming approach: HashingVectorizer + SGDClassifier.

    Returns (vectorizer, classifier)
    """
    X = df["text"].tolist()
    y = df["label"].tolist()

    # split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    X_train, y_train = apply_enhancement_oversampling(
        X_train,
        y_train,
        enhancement_df,
        args.enhancement_multiplier,
        args.phishing_enhancement_multiplier,
        args.false_positive_enhancement_multiplier,
    )
    print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples\n")

    print("Streaming training (HashingVectorizer + SGDClassifier)...")
    vectorizer = HashingVectorizer(ngram_range=(1, 2), n_features=2 ** 18, alternate_sign=False)
    clf = SGDClassifier(loss="log_loss", random_state=RANDOM_STATE)

    batch_size = 50000
    classes = [0, 1]
    # Partial fit in batches
    for i in range(0, len(X_train), batch_size):
        X_batch = X_train[i : i + batch_size]
        y_batch = y_train[i : i + batch_size]
        X_vec = vectorizer.transform(X_batch)
        if i == 0:
            clf.partial_fit(X_vec, y_batch, classes=classes)
        else:
            clf.partial_fit(X_vec, y_batch)
        print(f"  Trained on batch {i}..{i+len(X_batch)}")

    # evaluate
    X_test_vec = vectorizer.transform(X_test)
    y_pred = clf.predict(X_test_vec)
    print("Evaluating on test set:")
    print_metrics(y_test, y_pred)

    # save model as a wrapped object so downstream scripts can call predict()/predict_proba()
    wrapped_model = WrappedModel(vectorizer, clf)
    joblib.dump(wrapped_model, args.model_path)
    print(f"Model saved to: {args.model_path}")
    return vectorizer, clf


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
    if args.dataset_paths:
        print(f"Using dataset paths: {args.dataset_paths}")
    else:
        print("Using synthetic dataset")

    df = generate_dataset(dataset_paths=args.dataset_paths)
    enhancement_df = load_enhancement_rows(args.dataset_paths)
    if not enhancement_df.empty:
        print(f"Enhancement rows available for weighting: {len(enhancement_df)}")

    # Auto fallback to streaming for very large datasets to avoid memory/timeouts
    use_streaming = args.streaming or len(df) > 300_000
    if use_streaming:
        streaming_train(df, enhancement_df, args)
        return

    X = df["text"].tolist()
    y = df["label"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    X_train, y_train = apply_enhancement_oversampling(
        X_train,
        y_train,
        enhancement_df,
        args.enhancement_multiplier,
        args.phishing_enhancement_multiplier,
        args.false_positive_enhancement_multiplier,
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
