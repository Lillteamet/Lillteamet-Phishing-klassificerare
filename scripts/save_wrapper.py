"""Convert a streaming-trained model dict into a pipeline-like wrapped object.

Usage:
    python save_wrapper.py --input phishing_model.joblib --output phishing_model_wrapped.joblib

If the input is already a pipeline-like object, it will be copied to the output.
"""
from __future__ import annotations
import argparse
import joblib
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scripts.model_wrappers import WrappedModel


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="phishing_model.joblib")
    p.add_argument("--output", default="phishing_model_wrapped.joblib")
    args = p.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        raise SystemExit(f"Input model not found: {in_path}")

    m = joblib.load(in_path)
    # If already has predict(), just save it
    if hasattr(m, "predict") and hasattr(m, "predict_proba"):
        joblib.dump(m, out_path)
        print(f"Copied existing model to: {out_path}")
        return

    # Expect dict with 'vectorizer' and 'clf'
    if isinstance(m, dict) and "vectorizer" in m and "clf" in m:
        wrapped = WrappedModel(m["vectorizer"], m["clf"])
        joblib.dump(wrapped, out_path)
        print(f"Wrapped model written to: {out_path}")
        return

    raise SystemExit("Unsupported model format: expected pipeline-like object or dict with 'vectorizer' and 'clf'.")


if __name__ == "__main__":
    main()
