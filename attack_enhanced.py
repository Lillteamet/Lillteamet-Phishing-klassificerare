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
    python attack.py --email-file sample_email.txt
"""

import argparse
from pathlib import Path

import joblib
import numpy as np

from generate_data import generate_dataset

MODEL_PATH = "phishing_model.joblib"

# Words that the TF-IDF model treats as strong phishing signals,
# paired with innocuous replacements that preserve surface meaning.
SUBSTITUTIONS = [
    ("click here", "visit the page"),
    ("verify your", "review your"),
    ("verify your account", "review your profile"),
    ("temporarily blocked", "temporarily limited"),
    ("blocked your account", "limited your profile"),
    ("unblock your account", "restore your profile"),
    ("unusual activity", "recent activity"),
    ("terms of service", "service terms"),
    ("customer support", "help desk"),
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


def apply_substitution(text: str, trigger: str, replacement: str) -> tuple[str, bool]:
    """Replace one trigger phrase with a benign synonym."""
    lowered = text.lower()
    if trigger.lower() not in lowered:
        return text, False
    return lowered.replace(trigger.lower(), replacement.lower()), True


def apply_substitutions(text: str, substitutions: list[tuple[str, str]]) -> tuple[str, list[tuple[str, str]]]:
    """Replace trigger words with benign synonyms and return applied changes."""
    result = text
    applied = []
    for trigger, replacement in substitutions:
        result, changed = apply_substitution(result, trigger, replacement)
        if changed:
            applied.append((trigger, replacement))
    return result, applied


def find_victim(pipeline, texts: list[str], labels: list[int]) -> str | None:
    """Return the first phishing email correctly classified with confidence > 0.85."""
    for text, label in zip(texts, labels):
        if label != 1:
            continue
        pred_label, confidence = predict_with_confidence(pipeline, text)
        if pred_label == "PHISHING" and confidence > 0.85:
            return text
    return None


def evade(pipeline, original: str) -> tuple[str, list[dict], bool]:
    """
    Iteratively perturb the email until the model flips to HAM.
    Returns (final_text, attack_steps, success).
    """
    steps = []
    candidate = original

    # Apply substitutions one by one so we can see how confidence changes.
    for trigger, replacement in SUBSTITUTIONS:
        candidate, changed = apply_substitution(candidate, trigger, replacement)
        if not changed:
            continue
        label, confidence = predict_with_confidence(pipeline, candidate)
        steps.append({
            "action": f'replaced "{trigger}" -> "{replacement}"',
            "label": label,
            "confidence": confidence,
        })
        if label == "HAM":
            return candidate, steps, True

    # Append filler sentences one by one until the model flips
    substituted_candidate = candidate
    filler_buf = ""
    for sentence in FILLER_SENTENCES:
        filler_buf += " " + sentence
        candidate_with_filler = substituted_candidate + "\n\n" + filler_buf.strip()
        label, confidence = predict_with_confidence(pipeline, candidate_with_filler)
        steps.append({
            "action": f'added filler: "{sentence}"',
            "label": label,
            "confidence": confidence,
        })
        if label == "HAM":
            return candidate_with_filler, steps, True
        candidate = candidate_with_filler

    return candidate, steps, False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an evasion attack against the phishing classifier.")
    parser.add_argument(
        "--email-file",
        help="Optional email text file to attack instead of choosing a generated phishing sample.",
    )
    parser.add_argument(
        "--model-path",
        default=MODEL_PATH,
        help="Path to the trained model file.",
    )
    return parser.parse_args()


def load_victim_from_file(path: str) -> str:
    email_path = Path(path)
    if not email_path.exists():
        raise FileNotFoundError(f"Email file not found: {email_path}")
    return email_path.read_text(encoding="utf-8")


def main():
    args = parse_args()
    print("Loading model from:", args.model_path)
    pipeline = joblib.load(args.model_path)

    if args.email_file:
        print("Loading email from:", args.email_file)
        victim = load_victim_from_file(args.email_file)
    else:
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

    perturbed, steps, success = evade(pipeline, victim)

    print("=" * 60)
    print("ATTACK STEPS:")
    print("-" * 60)
    if not steps:
        print("No configured trigger phrases were found in the email.")
    for idx, step in enumerate(steps, start=1):
        print(f"{idx}. {step['action']}")
        print(f"   Prediction: {step['label']}  (confidence: {step['confidence']:.2%})")
    print()

    perturbed_label, perturbed_conf = predict_with_confidence(pipeline, perturbed)
    print("=" * 60)
    print("FINAL MODIFIED EMAIL (after adversarial perturbation):")
    print("-" * 60)
    print(perturbed)
    print("-" * 60)
    print(f"Prediction: {perturbed_label}  (confidence: {perturbed_conf:.2%})")
    print(f"Confidence change: {original_conf:.2%} -> {perturbed_conf:.2%}")
    print()
    print("=" * 60)
    if success:
        print("EVASION SUCCESSFUL: model flipped from PHISHING to HAM.")
        print("The email content is still malicious, but the classifier was fooled.")
    else:
        print("Attack failed: model did not flip with available perturbations.")
        print("The attack may still be useful if confidence dropped.")
    print("=" * 60)


if __name__ == "__main__":
    main()
