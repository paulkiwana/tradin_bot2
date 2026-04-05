#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python not found."
  exit 1
fi

echo "Starting Crypto Monitor - Auto Discovery (Console)..."
"$PYTHON" crypto_monitor_auto.py
