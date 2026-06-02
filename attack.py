"""
attack.py -- Adversarial evasion demo for the phishing classifier.

Strategy: feature-space substitution attack.
- Find a phishing email the model classifies correctly with high confidence.
- Iteratively swap the most "phishing-like" trigger words for benign synonyms
  and append innocuous filler sentences until the model flips to HAM.
- Print the original and modified email with prediction labels so the flip
  is obvious.

This is intentionally simple and illustrative: it shows that keyword-based
classifiers are vulnerable to surface-level perturbations.

Run:
    python attack.py
"""

import joblib
import numpy as np

from generate_data import generate_dataset

MODEL_PATH = "phishing_model.joblib"

# Words that the TF-IDF model treats as strong phishing signals,
# paired with innocuous replacements that preserve surface meaning.
SUBSTITUTIONS = [
    ("click here", "visit the page"),
    ("verify your", "review your"),
    ("suspended", "on hold"),
    ("urgent", "upcoming"),
    ("immediately", "soon"),
    ("password", "credentials"),
    ("account has been", "account is"),
    ("your account", "your profile"),
    ("action required", "action needed"),
    ("confirm your", "update your"),
    ("bank details", "payment preferences"),
    ("claim your", "check your"),
    ("compromised", "reviewed"),
    ("suspended", "paused"),
    ("terminate", "close"),
    ("penalty", "charge"),
    ("expire", "renew"),
    ("warning", "notice"),
    ("limited time", "available"),
    ("provide your", "share your"),
]

# Filler sentences that look like normal correspondence.
FILLER_SENTENCES = [
    "Hope this message finds you well.",
    "Please feel free to reach out if you have any questions.",
    "Have a great rest of your week.",
    "Looking forward to hearing from you.",
    "Best regards from the team.",
    "Thanks for your continued support.",
    "Let me know if there is anything I can help with.",
    "We appreciate your patience.",
    "Have a wonderful day.",
    "Kind regards.",
]


def predict_with_confidence(pipeline, text: str) -> tuple[str, float]:
    """Return (label_str, confidence) for a single email text."""
    proba = pipeline.predict_proba([text])[0]
    label_idx = int(np.argmax(proba))
    confidence = proba[label_idx]
    label_str = "PHISHING" if label_idx == 1 else "HAM"
    return label_str, confidence


def apply_substitutions(text: str, substitutions: list[tuple[str, str]]) -> str:
    """Replace trigger words with benign synonyms (case-insensitive)."""
    result = text
    for trigger, replacement in substitutions:
        result = result.lower().replace(trigger.lower(), replacement.lower())
    return result


def find_victim(pipeline, texts: list[str], labels: list[int]) -> str | None:
    """Return the first phishing email correctly classified with confidence > 0.85."""
    for text, label in zip(texts, labels):
        if label != 1:
            continue
        pred_label, confidence = predict_with_confidence(pipeline, text)
        if pred_label == "PHISHING" and confidence > 0.85:
            return text
    return None


def evade(pipeline, original: str) -> str | None:
    """
    Iteratively perturb the email until the model flips to HAM.
    Returns the perturbed text, or None if evasion failed.
    """
    candidate = apply_substitutions(original, SUBSTITUTIONS)

    # Check after substitutions alone
    label, _ = predict_with_confidence(pipeline, candidate)
    if label == "HAM":
        return candidate

    # Append filler sentences one by one until the model flips
    filler_buf = ""
    for sentence in FILLER_SENTENCES:
        filler_buf += " " + sentence
        candidate_with_filler = candidate + "\n\n" + filler_buf.strip()
        label, _ = predict_with_confidence(pipeline, candidate_with_filler)
        if label == "HAM":
            return candidate_with_filler

    return None  # Attack did not succeed with available perturbations


def main():
    print("Loading model from:", MODEL_PATH)
    pipeline = joblib.load(MODEL_PATH)

    print("Searching for a correctly-classified phishing email to attack...\n")
    df = generate_dataset()
    texts = df["text"].tolist()
    labels = df["label"].tolist()

    victim = find_victim(pipeline, texts, labels)
    if victim is None:
        print("ERROR: Could not find a suitable victim email. Re-train the model first.")
        return

    original_label, original_conf = predict_with_confidence(pipeline, victim)
    print("=" * 60)
    print("ORIGINAL EMAIL (before attack):")
    print("-" * 60)
    print(victim)
    print("-" * 60)
    print(f"Prediction: {original_label}  (confidence: {original_conf:.2%})")
    print()

    perturbed = evade(pipeline, victim)

    if perturbed is None:
        print("Attack failed: model did not flip with available perturbations.")
        return

    perturbed_label, perturbed_conf = predict_with_confidence(pipeline, perturbed)
    print("=" * 60)
    print("MODIFIED EMAIL (after adversarial perturbation):")
    print("-" * 60)
    print(perturbed)
    print("-" * 60)
    print(f"Prediction: {perturbed_label}  (confidence: {perturbed_conf:.2%})")
    print()
    print("=" * 60)
    if perturbed_label == "HAM":
        print("EVASION SUCCESSFUL: model flipped from PHISHING to HAM.")
        print("The email content is still malicious, but the classifier was fooled.")
    else:
        print("Evasion did not succeed with current perturbations.")
    print("=" * 60)


if __name__ == "__main__":
    main()
