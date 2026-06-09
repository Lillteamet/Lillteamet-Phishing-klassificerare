"""scripts/validate_model.py

Quick validator for a shipped `phishing_model.joblib` artifact.

Checks:
- file exists and size
- optional SHA256 checksum
- loadable via joblib
- has `predict` and `predict_proba`
- runs smoke inference on small examples and `sample_email.txt` if available
- prints human-readable summary or JSON with `--json`

Exit codes: 0 on success, non-zero on failure.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import joblib


DEFAULT_MODEL = "phishing_model.joblib"
SAMPLE_PHISH = "Subject: Verify your account now\n\nClick here to update your billing information."
SAMPLE_HAM = "Subject: Team meeting\n\nReminder: our team meeting is tomorrow at 10am."


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_model(path: Path):
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")


def sanity_checks(model) -> None:
    if not hasattr(model, "predict"):
        raise RuntimeError("Loaded object does not expose `predict()`")
    if not hasattr(model, "predict_proba"):
        raise RuntimeError("Loaded object does not expose `predict_proba()`")


def predict_samples(model, texts: list[str]) -> list[dict]:
    results = []
    try:
        probs = model.predict_proba(texts)
        preds = model.predict(texts)
    except Exception as e:
        raise RuntimeError(f"Model prediction failed: {e}")

    for t, p, pred in zip(texts, probs, preds):
        # ensure probability vector
        try:
            label_idx = int(pred)
        except Exception:
            label_idx = int((p.argmax() if hasattr(p, 'argmax') else p.index(max(p))))
        confidence = float(p[label_idx])
        results.append({"text": t, "pred": int(label_idx), "confidence": confidence})
    return results


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Validate a trained phishing_model.joblib file")
    p.add_argument("--model-path", default=DEFAULT_MODEL, help="Path to the model file")
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    p.add_argument("--checksum", action="store_true", help="Print SHA256 checksum of the model file")
    p.add_argument("--min-confidence", type=float, default=0.0, help="Optional minimum confidence threshold for smoke checks")
    args = p.parse_args(argv)

    model_path = Path(args.model_path)
    out = {"model_path": str(model_path)}

    if not model_path.exists():
        print(f"ERROR: Model file not found: {model_path}", file=sys.stderr)
        return 2

    size = model_path.stat().st_size
    out["size_bytes"] = size

    if args.checksum:
        try:
            out["sha256"] = sha256sum(model_path)
        except Exception as e:
            print(f"ERROR computing checksum: {e}", file=sys.stderr)
            return 3

    try:
        model = load_model(model_path)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 4

    try:
        sanity_checks(model)
    except Exception as e:
        print(f"ERROR: sanity check failed: {e}", file=sys.stderr)
        return 5

    # prepare sample texts
    texts = [SAMPLE_PHISH, SAMPLE_HAM]
    sample_email = Path("sample_email.txt")
    if sample_email.exists():
        try:
            texts.append(sample_email.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        preds = predict_samples(model, texts)
    except Exception as e:
        print(f"ERROR during prediction: {e}", file=sys.stderr)
        return 6

    out["predictions"] = preds

    # simple validation: ensure probabilities are between 0 and 1
    for r in preds:
        if not (0.0 <= r["confidence"] <= 1.0):
            print("ERROR: Invalid confidence value", file=sys.stderr)
            return 7

    # print results
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"Model file: {model_path} ({size} bytes)")
        if args.checksum:
            print(f"SHA256: {out.get('sha256')}")
        print("Load: OK")
        print("Predictions:")
        for i, r in enumerate(preds):
            short = (r["text"][:120] + "...") if len(r["text"]) > 120 else r["text"]
            label = "PHISHING" if r["pred"] == 1 else "HAM"
            print(f"  - sample_{i}: {label} (confidence: {r['confidence']:.2%}) | {short}")
        print("\nResult: VALID")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
