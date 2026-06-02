"""
train.py -- Train a phishing email classifier and save it to disk.

Pipeline: TF-IDF vectorizer -> Logistic Regression
Outputs:  accuracy, precision, recall, F1 to stdout
Saves:    phishing_model.joblib (the fitted pipeline)

Run:
    python train.py
"""

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
    print("Loading dataset...")
    df = generate_dataset()
    X = df["text"].tolist()
    y = df["label"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples\n")

    print("Training pipeline (TF-IDF + Logistic Regression)...")
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    print("Evaluating on test set:")
    y_pred = pipeline.predict(X_test)
    print_metrics(y_test, y_pred)

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
