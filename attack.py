"""
attack.py -- Adversarial evasion demos for the phishing classifier.

Modes:
- baseline: simple keyword substitutions plus benign filler text.
- adaptive: larger phishing-style rewrites with softer language and URL obfuscation.

Run:
    python attack.py
    python attack.py --mode baseline --email-file sample_email.txt
    python attack.py --mode adaptive --email-file sample_email.txt
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from generate_data import generate_dataset

MODEL_PATH = "phishing_model.joblib"

BASELINE_SUBSTITUTIONS = [
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
        description="Run an evasion attack demo against the phishing classifier."
    )
    parser.add_argument(
        "--mode",
        choices=["baseline", "adaptive"],
        default="baseline",
        help="Attack mode to run.",
    )
    parser.add_argument(
        "--email-file",
        help="Optional email text file to use as the original phishing message.",
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


def load_email_file(path: str) -> str:
    email_path = Path(path)
    if not email_path.exists():
        raise FileNotFoundError(f"Email file not found: {email_path}")
    return email_path.read_text(encoding="utf-8", errors="replace")


def find_victim(model, texts: list[str], labels: list[int]) -> str | None:
    """Return the first phishing email correctly classified with confidence > 0.85."""
    for text, label in zip(texts, labels):
        if label != 1:
            continue
        pred_label, confidence = predict_with_confidence(model, text)
        if pred_label == "PHISHING" and confidence > 0.85:
            return text
    return None


def apply_substitutions(text: str, substitutions: list[tuple[str, str]]) -> str:
    result = text
    for trigger, replacement in substitutions:
        result = result.lower().replace(trigger.lower(), replacement.lower())
    return result


def run_baseline_attack(model, original: str) -> tuple[str, list[dict], bool]:
    steps = []
    candidate = apply_substitutions(original, BASELINE_SUBSTITUTIONS)
    label, confidence = predict_with_confidence(model, candidate)
    steps.append({
        "action": "applied baseline keyword substitutions",
        "label": label,
        "confidence": confidence,
    })
    if label == "HAM":
        return candidate, steps, True

    filler_buf = ""
    for sentence in FILLER_SENTENCES:
        filler_buf += " " + sentence
        candidate_with_filler = candidate + "\n\n" + filler_buf.strip()
        label, confidence = predict_with_confidence(model, candidate_with_filler)
        steps.append({
            "action": f'added filler: "{sentence}"',
            "label": label,
            "confidence": confidence,
        })
        if label == "HAM":
            return candidate_with_filler, steps, True

    return candidate_with_filler, steps, False


def score_adaptive_candidate(model, candidate: AttackCandidate) -> AttackCandidate:
    label, confidence = predict_with_confidence(model, candidate.text)
    return AttackCandidate(
        name=candidate.name,
        steps=candidate.steps,
        text=candidate.text,
        label=label,
        confidence=confidence,
    )


def run_adaptive_attack(model) -> tuple[AttackCandidate, list[AttackCandidate], bool]:
    scored = [score_adaptive_candidate(model, candidate) for candidate in ADAPTIVE_REWRITES]
    best = sorted(scored, key=lambda candidate: candidate.success_rank)[0]
    return best, scored, best.label == "HAM"


def print_email_block(title: str, text: str, label: str, confidence: float) -> None:
    print("=" * 60)
    print(title)
    print("-" * 60)
    print(text)
    print("-" * 60)
    print(f"Prediction: {label}  (confidence: {confidence:.2%})")
    print()


def load_original_for_mode(model, args: argparse.Namespace) -> str:
    if args.email_file:
        return load_email_file(args.email_file)

    if args.mode == "adaptive":
        default_email = Path("sample_email.txt")
        if default_email.exists():
            return default_email.read_text(encoding="utf-8", errors="replace")

    print("Searching for a correctly-classified phishing email to attack...\n")
    df = generate_dataset()
    victim = find_victim(model, df["text"].tolist(), df["label"].tolist())
    if victim is None:
        raise RuntimeError("Could not find a suitable victim email. Re-train the model first.")
    return victim


def main() -> None:
    args = parse_args()
    print("Loading model from:", args.model_path)
    model = joblib.load(args.model_path)

    original = load_original_for_mode(model, args)
    original_label, original_confidence = predict_with_confidence(model, original)
    print_email_block(
        f"ORIGINAL EMAIL (before {args.mode} attack)",
        original,
        original_label,
        original_confidence,
    )

    if args.mode == "baseline":
        final_text, steps, success = run_baseline_attack(model, original)

        print("=" * 60)
        print("BASELINE ATTACK STEPS")
        print("-" * 60)
        for index, step in enumerate(steps, start=1):
            print(f"{index}. {step['action']}")
            print(f"   Prediction: {step['label']}  (confidence: {step['confidence']:.2%})")
        print()

        final_label, final_confidence = predict_with_confidence(model, final_text)
        print_email_block(
            "FINAL MODIFIED EMAIL (after baseline perturbation)",
            final_text,
            final_label,
            final_confidence,
        )
    else:
        best, scored, success = run_adaptive_attack(model)

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

        final_text = best.text
        final_label = best.label
        final_confidence = best.confidence
        print_email_block(
            "FINAL MODIFIED EMAIL (after adaptive rewrite)",
            final_text,
            final_label,
            final_confidence,
        )

    print(f"Confidence change: {original_confidence:.2%} -> {final_confidence:.2%}")
    print()
    print("=" * 60)
    if original_label == "PHISHING" and success:
        print("EVASION SUCCESSFUL: model flipped from PHISHING to HAM.")
        print("This is a controlled simulated attack for defensive testing.")
    else:
        print("Attack failed: the selected rewrite did not flip the model to HAM.")
    print("=" * 60)


if __name__ == "__main__":
    main()
