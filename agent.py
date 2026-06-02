"""
agent.py -- Phishing email scanner agent.

This script loads the saved phishing classifier and scans a raw email
text for known phishing signatures and suspicious patterns.

It prints a prediction, confidence score, matched signatures, and a short
assumption why the email may be phishing.

Run:
    python agent.py --text "Subject: ..."
    python agent.py --email-file sample_email.txt
"""

import argparse
import re
from pathlib import Path

import joblib
import numpy as np

MODEL_PATH = "phishing_model.joblib"

SIGNATURE_PATTERNS = [
    (r"click here", "direct call-to-action to click a link"),
    (r"verify your", "request to verify sensitive account details"),
    (r"account has been suspended", "account suspension scare tactic"),
    (r"urgent", "urgency pressure to act quickly"),
    (r"password", "request for credentials or sensitive login data"),
    (r"confirm your", "request for confirmation of private information"),
    (r"bank details", "request for financial account information"),
    (r"claim your", "offer-based lure to capture personal data"),
    (r"compromised", "security breach scare wording"),
    (r"limited time", "time-limited pressure often used in scams"),
    (r"payment failed", "billing-related phishing message"),
    (r"security alert", "security scare used to force action"),
    (r"invoice payment is overdue", "payment reminder phrasing common in phishing"),
    (r"your account has been suspended", "account lockout threat"),
    (r"confirm your identity", "identity verification request"),
    (r"billing information", "sensitive payment request"),
    (r"social security number", "highly sensitive personal data requested"),
    (r"update your billing", "payment update lure"),
    (r"verify now", "urgent verification demand"),
    (r"receive your item", "delivery scam phrasing"),
]

URL_PATTERN = re.compile(r"https?://[^"]+", flags=re.IGNORECASE)
GENERIC_PHISHING_PATTERNS = [
    (re.compile(r"dear\s+customer", re.IGNORECASE), "generic greeting often used by phishing emails"),
    (re.compile(r"suspended|terminated|closed|limited time|expire|expired", re.IGNORECASE), "threat or expiry language"),
    (re.compile(r"(payment|billing|invoice).*(details|information|failed)", re.IGNORECASE), "financial urgency or payment request"),
    (re.compile(r"(security|verification).*(alert|issue|problem|breach)", re.IGNORECASE), "security alert wording"),
]


class PhishingAgent:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = Path(model_path)
        self.pipeline = None

    def load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}. Train the model first with python train.py"
            )
        self.pipeline = joblib.load(self.model_path)

    def predict(self, text: str) -> tuple[str, float]:
        proba = self.pipeline.predict_proba([text])[0]
        label_idx = int(np.argmax(proba))
        label = "PHISHING" if label_idx == 1 else "HAM"
        confidence = float(proba[label_idx])
        return label, confidence

    def scan(self, text: str) -> dict:
        if self.pipeline is None:
            self.load_model()

        label, confidence = self.predict(text)
        lower_text = text.lower()

        matches = []
        for pattern, reason in SIGNATURE_PATTERNS:
            if pattern in lower_text:
                matches.append((pattern, reason))

        for regex, reason in GENERIC_PHISHING_PATTERNS:
            if regex.search(text):
                matches.append((regex.pattern, reason))

        urls = URL_PATTERN.findall(text)
        if urls:
            matches.append(("url", f"contains suspicious link(s): {', '.join(urls[:3])}"))

        assumptions = []
        if label == "PHISHING":
            assumptions.append("The model predicts this is phishing.")
        else:
            assumptions.append("The model predicts this is ham (legitimate).")

        if matches:
            assumptions.append(
                "Detected signature patterns that are often associated with phishing emails."
            )
        else:
            assumptions.append(
                "No strong phishing signatures were detected, so the prediction is based on the overall text patterns."
            )

        return {
            "label": label,
            "confidence": confidence,
            "matches": matches,
            "assumptions": assumptions,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a raw email text for phishing signals using the trained classifier."
    )
    parser.add_argument(
        "--model-path",
        default=MODEL_PATH,
        help="Path to the trained model file (default: phishing_model.joblib).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email-file", help="Path to a plain text file containing the email to scan.")
    group.add_argument("--text", help="Raw email text to scan.")
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Print the scan result as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def print_scan_result(result: dict) -> None:
    print(f"Prediction: {result['label']}  (confidence: {result['confidence']:.2%})")
    print()
    if result["matches"]:
        print("Detected signatures and suspicious patterns:")
        for pattern, reason in result["matches"]:
            print(f"  - {pattern}: {reason}")
    else:
        print("No known phishing signatures were detected.")
    print()
    print("Assumptions:")
    for assumption in result["assumptions"]:
        print(f"  - {assumption}")


def main() -> None:
    args = parse_args()
    agent = PhishingAgent(model_path=args.model_path)
    agent.load_model()

    if args.email_file:
        email_path = Path(args.email_file)
        if not email_path.exists():
            raise FileNotFoundError(f"Email file not found: {email_path}")
        text = email_path.read_text(encoding="utf-8")
    else:
        text = args.text

    result = agent.scan(text)

    if args.show_json:
        import json

        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_scan_result(result)


if __name__ == "__main__":
    main()
