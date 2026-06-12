#!/usr/bin/env bash
set -euo pipefail
rm -f validation_report.txt
python scripts/validate_pipeline.py --output validation_report.txt