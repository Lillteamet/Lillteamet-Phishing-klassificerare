"""
attack_training_generator.py -- Generate hard phishing examples for retraining.

This tool creates simulated phishing emails, mutates them with evasion-style
wording, tests each candidate against phishing_model.joblib, and saves the
hardest phishing examples under Datasets/enhancements/phishing/.

The saved examples are intended as defensive retraining data. They are labeled
as phishing by directory placement, even when the current model predicts HAM.

Run:
    python attack_training_generator.py --dry-run --candidates 40 --limit 8
    python attack_training_generator.py --candidates 40 --limit 8
    python attack_training_generator.py --email-file sample_email.txt --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np

MODEL_PATH = "phishing_model.joblib"
DEFAULT_OUTPUT_DIR = "Datasets/enhancements/phishing"


BASE_PHISHING_EMAILS = [
    """Subject: review your profile now

Dear customer,

We detected recent activity on your profile. Visit the page to review your billing information soon and avoid service interruption.

Best regards,
Help Desk Team""",
    """Subject: account service notice

Hello,

Your account requires a quick profile review. Please open the secure message center and update your payment preferences to keep service active.

Regards,
Customer Care""",
    """Subject: delivery preference update

Dear user,

A package delivery is waiting for address confirmation. Please review the delivery page and confirm the small handling fee so the item can be released.

Kind regards,
Delivery Support""",
    """Subject: workspace access check

Hi,

We noticed a sign-in attempt from a new location. Please review your access settings and confirm your credentials to avoid a temporary limitation.

Support Team""",
]

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
    ("terminate", "close"),
    ("penalty", "charge"),
    ("expire", "renew"),
    ("warning", "notice"),
    ("limited time", "available"),
    ("provide your", "share your"),
]

SUBJECTS = [
    "Subject: profile service notice",
    "Subject: update pending in message center",
    "Subject: access review requested",
    "Subject: billing preference check",
    "Subject: delivery release update",
    "Subject: customer support follow-up",
]

GREETINGS = [
    "Dear customer,",
    "Hello,",
    "Hi,",
    "Dear user,",
]

ACTION_LINES = [
    "Please review the secure message center and keep your profile information current.",
    "Open the account page and update the requested details before the next service cycle.",
    "Use the support page to confirm the pending profile review.",
    "Review your access settings so the service can continue without interruption.",
    "Confirm the delivery details and small handling fee to release the item.",
]

SOFT_URGENCY_LINES = [
    "This should be completed soon to avoid delays.",
    "The review is available for a short period.",
    "Your service may be limited until the review is complete.",
    "The pending notice will remain open today.",
]

LINK_LINES = [
    "Reference: https://support.example.com/profile-review",
    "Reference: https://account.example.com/message-center",
    "Reference: hxxps://support[.]example[.]com/access",
    "Reference code: CASE-74291",
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
]

SIGNOFFS = [
    "Best regards,\nHelp Desk Team",
    "Kind regards,\nCustomer Care",
    "Regards,\nSupport Team",
]


@dataclass(frozen=True)
class ScoredCandidate:
    text: str
    label: str
    confidence: float

    @property
    def rank_key(self) -> tuple[int, float]:
        if self.label == "HAM":
            return (0, -self.confidence)
        return (1, self.confidence)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate model-hard phishing examples for defensive retraining."
    )
    parser.add_argument(
        "--model-path",
        default=MODEL_PATH,
        help="Path to the trained model artifact.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where generated phishing examples are saved.",
    )
    parser.add_argument(
        "--email-file",
        action="append",
        default=[],
        help="Optional phishing seed email file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=40,
        help="Number of mutated candidates to test.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Maximum number of hard examples to save.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.75,
        help="Also keep PHISHING predictions at or below this confidence.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible candidate generation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected examples without writing files.",
    )
    return parser.parse_args()


def predict_with_confidence(model, text: str) -> tuple[str, float]:
    proba = model.predict_proba([text])[0]
    label_idx = int(np.argmax(proba))
    label = "PHISHING" if label_idx == 1 else "HAM"
    confidence = float(proba[label_idx])
    return label, confidence


def load_seed_emails(paths: list[str]) -> list[str]:
    seeds = list(BASE_PHISHING_EMAILS)
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"Seed email file not found: {path}")
        seeds.append(path.read_text(encoding="utf-8", errors="replace"))
    return seeds


def apply_substitutions(text: str, rng: random.Random) -> str:
    candidate = text
    shuffled = list(SUBSTITUTIONS)
    rng.shuffle(shuffled)
    for trigger, replacement in shuffled[: rng.randint(6, len(shuffled))]:
        candidate = candidate.replace(trigger, replacement)
        candidate = candidate.replace(trigger.title(), replacement)
        candidate = candidate.replace(trigger.capitalize(), replacement)
    return candidate


def compose_candidate(seed_text: str, rng: random.Random) -> str:
    if rng.random() < 0.45:
        body_lines = [
            rng.choice(SUBJECTS),
            "",
            rng.choice(GREETINGS),
            "",
            rng.choice(ACTION_LINES),
            rng.choice(SOFT_URGENCY_LINES),
        ]
        if rng.random() < 0.70:
            body_lines.extend(["", rng.choice(LINK_LINES)])
        body_lines.extend(["", rng.choice(SIGNOFFS)])
        candidate = "\n".join(body_lines)
    else:
        candidate = seed_text

    candidate = apply_substitutions(candidate, rng)

    filler_count = rng.randint(1, min(6, len(FILLER_SENTENCES)))
    filler = " ".join(rng.sample(FILLER_SENTENCES, filler_count))
    if rng.random() < 0.80:
        candidate = f"{candidate}\n\n{filler}"

    return candidate.strip()


def generate_candidates(seed_texts: list[str], count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    candidates = []
    seen_hashes = set()

    while len(candidates) < count:
        candidate = compose_candidate(rng.choice(seed_texts), rng)
        digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        candidates.append(candidate)

    return candidates


def select_hard_examples(
    model,
    candidates: list[str],
    limit: int,
    confidence_threshold: float,
) -> list[ScoredCandidate]:
    scored = []
    for candidate in candidates:
        label, confidence = predict_with_confidence(model, candidate)
        if label == "HAM" or confidence <= confidence_threshold:
            scored.append(ScoredCandidate(candidate, label, confidence))

    return sorted(scored, key=lambda item: item.rank_key)[:limit]


def format_training_example(candidate: ScoredCandidate) -> str:
    return (
        "# Simulated phishing example generated by attack_training_generator.py.\n"
        "# Reason saved: current model classified this phishing-style email as "
        f"{candidate.label} with {candidate.confidence:.2%} confidence.\n"
        "# Expected label for retraining: phishing\n\n"
        f"{candidate.text}\n"
    )


def write_examples(examples: list[ScoredCandidate], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    written = []

    for index, example in enumerate(examples, start=1):
        digest = hashlib.sha256(example.text.encode("utf-8")).hexdigest()[:10]
        path = output_dir / f"generated_evasion_{timestamp}_{index:02d}_{digest}.txt"
        path.write_text(format_training_example(example), encoding="utf-8")
        written.append(path)

    return written


def main() -> None:
    args = parse_args()
    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. Train the model first or place phishing_model.joblib in the repo root."
        )

    if args.candidates < 1:
        raise ValueError("--candidates must be at least 1")
    if args.limit < 1:
        raise ValueError("--limit must be at least 1")

    print(f"Loading model from: {model_path}")
    model = joblib.load(model_path)

    seed_texts = load_seed_emails(args.email_file)
    candidates = generate_candidates(seed_texts, args.candidates, args.seed)
    selected = select_hard_examples(
        model,
        candidates,
        limit=args.limit,
        confidence_threshold=args.confidence_threshold,
    )

    print(f"Generated candidates: {len(candidates)}")
    print(f"Selected hard examples: {len(selected)}")

    if not selected:
        print("No candidates met the hard-example criteria.")
        return

    for index, example in enumerate(selected, start=1):
        print(f"{index}. {example.label} ({example.confidence:.2%})")
        if args.dry_run:
            print("-" * 60)
            print(format_training_example(example).rstrip())
            print("-" * 60)

    if args.dry_run:
        print("Dry run: no files written.")
        return

    written = write_examples(selected, Path(args.output_dir))
    print("Wrote files:")
    for path in written:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
