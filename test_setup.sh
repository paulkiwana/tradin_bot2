#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python not found. Install Python 3.8+ or run ./setup.sh first."
  exit 1
fi

echo "Running system tests..."
"$PYTHON" test_monitor.py
