"""scripts/validate_pipeline.py

Run the agent/data validation workflow and export a human-readable report.

This script executes the key workflow steps:
  - `python train.py --dataset-paths Datasets`
  - dataset parsing summary via `generate_data.generate_dataset`
  - `python scripts/validate_model.py --model-path phishing_model.joblib`
  - `python agent.py --email-file sample_email.txt`
  - `python attack.py`

Output is written to a text file for easy review or sharing.
"""

from __future__ import annotations
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from generate_data import generate_dataset


def run_command(cmd: list[str], cwd: Path) -> dict:
    process = subprocess.Popen(
        [sys.executable] + cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    assert process.stdout is not None
    assert process.stderr is not None

    while True:
        stdout_line = process.stdout.readline()
        stderr_line = process.stderr.readline()
        if stdout_line:
            stdout_lines.append(stdout_line.rstrip("\n"))
            print(stdout_line, end="")
        if stderr_line:
            stderr_lines.append(stderr_line.rstrip("\n"))
            print(stderr_line, end="")
        if stdout_line == "" and stderr_line == "" and process.poll() is not None:
            break

    return {
        "command": " ".join(cmd),
        "returncode": process.returncode,
        "stdout": "\n".join(stdout_lines).strip(),
        "stderr": "\n".join(stderr_lines).strip(),
    }


def format_command_block(section: str, result: dict) -> str:
    lines = [f"=== {section} ===", f"Command: {result['command']}", f"Return code: {result['returncode']}", ""]
    if result["stdout"]:
        lines.append("--- STDOUT ---")
        lines.extend(result["stdout"].splitlines())
        lines.append("")
    if result["stderr"]:
        lines.append("--- STDERR ---")
        lines.extend(result["stderr"].splitlines())
        lines.append("")
    return "\n".join(lines)


def dataset_summary(dataset_paths: list[str]) -> dict:
    df = generate_dataset(dataset_paths=dataset_paths)
    return {
        "rows": int(len(df)),
        "label_counts": df["label"].value_counts().to_dict(),
        "missing_text": int(df["text"].isna().sum()),
        "empty_text": int((df["text"].str.strip() == "").sum()),
        "sample_rows": [
            {"label": int(row["label"]), "text": str(row["text"][:200])}
            for _, row in df.head(5).iterrows()
        ],
    }


def _resolve_dataset_paths(dataset_paths: list[str] | None) -> list[str]:
    resolved = list(dataset_paths or ["Datasets"])
    enhancements_path = repo_root / "enhancements"
    if "enhancements" not in resolved and enhancements_path.exists():
        resolved.append("enhancements")
    return resolved


def build_report(args: argparse.Namespace) -> str:
    lines = [
        f"Validation report generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"Repository root: {repo_root}",
        "",
    ]

    dataset_paths = _resolve_dataset_paths(args.dataset_paths)
    # Step 1: training
    train_result = run_command(["train.py", "--dataset-paths", *dataset_paths], cwd=repo_root)
    lines.append(format_command_block("Train model", train_result))

    # Step 2: dataset summary
    lines.append("=== Dataset summary ===")
    try:
        summary = dataset_summary(dataset_paths)
        lines.append(f"rows: {summary['rows']}")
        lines.append(f"label_counts: {summary['label_counts']}")
        lines.append(f"missing text: {summary['missing_text']}")
        lines.append(f"empty text: {summary['empty_text']}")
        lines.append("")
        lines.append("Sample rows:")
        for row in summary["sample_rows"]:
            lines.append(f"  - label={row['label']} text={row['text']}")
        lines.append("")
    except Exception as exc:
        lines.append(f"Failed dataset summary: {exc}")
        lines.append("")

    # Step 3: validate model
    validate_result = run_command(["scripts/validate_model.py", "--model-path", args.model_path], cwd=repo_root)
    lines.append(format_command_block("Validate model", validate_result))

    # Step 4: agent scan
    agent_result = run_command(["agent.py", "--email-file", args.sample_email], cwd=repo_root)
    lines.append(format_command_block("Agent scan", agent_result))

    # Step 5: attack demo
    attack_result = run_command(["attack.py"], cwd=repo_root)
    lines.append(format_command_block("Attack demo", attack_result))

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full agent/data validation and export a human-readable report.")
    parser.add_argument(
        "--dataset-paths",
        nargs="+",
        default=None,
        help="Dataset directories or files to use for training and validation.",
    )
    parser.add_argument(
        "--model-path",
        default="phishing_model.joblib",
        help="Path to the trained model artifact.",
    )
    parser.add_argument(
        "--sample-email",
        default="sample_email.txt",
        help="Path to the sample email file for agent scanning.",
    )
    parser.add_argument(
        "--output",
        default="validation_report.txt",
        help="Path to write the human-readable validation report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    Path(args.output).write_text(report, encoding="utf-8")
    print(f"Validation report written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
