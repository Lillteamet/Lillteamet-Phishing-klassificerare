"""
attack_adaptive.py -- Adaptive evasion demo for defensive model testing.

This script is a controlled security test for the project classifier. It does
not modify training data and uses simulated example domains only.

Strategy:
- Load the current phishing classifier.
- Score the original phishing email.
- Try several larger phishing-style rewrites that reduce obvious signature
  words, soften urgency, and obfuscate the URL.
- Report the best candidate and whether the model flips to HAM.

Run:
    python attack_adaptive.py --email-file sample_email.txt
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

MODEL_PATH = "phishing_model.joblib"


@dataclass(frozen=True)
class AttackCandidate:
    name: str
    steps: list[str]
    text: str
    label: str = ""
    confidence: float = 0.0

    @property
    def success_rank(self) -> tuple[int, float]:
        if self.label == "HAM":
            return (0, -self.confidence)
        return (1, self.confidence)


ADAPTIVE_REWRITES = [
    AttackCandidate(
        name="soft_delivery_notice",
        steps=[
            "replace account/billing framing with delivery-release framing",
            "remove direct phishing keywords such as password, verify now, and click here",
            "use obfuscated example URL syntax",
        ],
        text="""Subject: profile service notice

Hi,

Confirm the delivery details and small handling fee to release the item.
The review is available for a short period.

Reference: hxxps://support[.]example[.]com/access

Regards,
Support Team""",
    ),
    AttackCandidate(
        name="support_follow_up",
        steps=[
            "rewrite as customer support follow-up",
            "move the request into a generic profile review",
            "add benign business-style filler text",
        ],
        text="""Subject: customer support follow-up

Dear user,

Use the support page to confirm the pending profile review.
This should be completed soon to avoid delays.

Reference: hxxps://support[.]example[.]com/access

Regards,
Support Team

Best regards from the team. Thanks for your continued support. Looking forward to hearing from you. Have a great rest of your week. Let me know if there is anything I can help with. Please feel free to reach out if you have any questions.""",
    ),
    AttackCandidate(
        name="access_review",
        steps=[
            "rewrite as access review request",
            "soften urgency language",
            "avoid high-weight billing and security-alert phrases",
        ],
        text="""Subject: access review requested

Hello,

Use the support page to confirm the pending profile review.
The review is available for a short period.

Regards,
Support Team

Have a great rest of your week. Please feel free to reach out if you have any questions. Let me know if there is anything I can help with. Thanks for your continued support. Looking forward to hearing from you. Hope this message finds you well.""",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an adaptive evasion demo against the phishing classifier."
    )
    parser.add_argument(
        "--email-file",
        default="sample_email.txt",
        help="Original phishing email to use as baseline.",
    )
    parser.add_argument(
        "--model-path",
        default=MODEL_PATH,
        help="Path to the trained model file.",
    )
    return parser.parse_args()


def predict_with_confidence(model, text: str) -> tuple[str, float]:
    proba = model.predict_proba([text])[0]
    label_idx = int(np.argmax(proba))
    label = "PHISHING" if label_idx == 1 else "HAM"
    confidence = float(proba[label_idx])
    return label, confidence


def score_candidate(model, candidate: AttackCandidate) -> AttackCandidate:
    label, confidence = predict_with_confidence(model, candidate.text)
    return AttackCandidate(
        name=candidate.name,
        steps=candidate.steps,
        text=candidate.text,
        label=label,
        confidence=confidence,
    )


def print_email_block(title: str, text: str, label: str, confidence: float) -> None:
    print("=" * 60)
    print(title)
    print("-" * 60)
    print(text)
    print("-" * 60)
    print(f"Prediction: {label}  (confidence: {confidence:.2%})")
    print()


def main() -> None:
    args = parse_args()
    model_path = Path(args.model_path)
    email_path = Path(args.email_file)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. Train the model first or place phishing_model.joblib in the repo root."
        )
    if not email_path.exists():
        raise FileNotFoundError(f"Email file not found: {email_path}")

    print("Loading model from:", model_path)
    model = joblib.load(model_path)

    original = email_path.read_text(encoding="utf-8", errors="replace")
    original_label, original_confidence = predict_with_confidence(model, original)
    print_email_block(
        "ORIGINAL EMAIL (before adaptive attack)",
        original,
        original_label,
        original_confidence,
    )

    scored = [score_candidate(model, candidate) for candidate in ADAPTIVE_REWRITES]
    best = sorted(scored, key=lambda candidate: candidate.success_rank)[0]

    print("=" * 60)
    print("ADAPTIVE ATTACK CANDIDATES")
    print("-" * 60)
    for index, candidate in enumerate(scored, start=1):
        print(f"{index}. {candidate.name}: {candidate.label} ({candidate.confidence:.2%})")
    print()

    print("=" * 60)
    print("SELECTED ATTACK STEPS")
    print("-" * 60)
    for index, step in enumerate(best.steps, start=1):
        print(f"{index}. {step}")
    print()

    print_email_block(
        "FINAL MODIFIED EMAIL (after adaptive rewrite)",
        best.text,
        best.label,
        best.confidence,
    )
    print(f"Confidence change: {original_confidence:.2%} -> {best.confidence:.2%}")
    print()
    print("=" * 60)
    if original_label == "PHISHING" and best.label == "HAM":
        print("EVASION SUCCESSFUL: model flipped from PHISHING to HAM.")
        print("This is a controlled simulated attack for defensive testing.")
    else:
        print("Attack failed: the selected rewrite did not flip the model to HAM.")
    print("=" * 60)


if __name__ == "__main__":
    main()
