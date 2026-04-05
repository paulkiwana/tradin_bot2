#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "============================================"
echo "Crypto Monitor Setup"
echo "============================================"
echo

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python is not installed or not in PATH"
  echo "Install Python 3.8+ from https://www.python.org/downloads/ or use Homebrew: brew install python"
  exit 1
fi

echo "Checking Python installation..."
"$PYTHON" --version
echo

echo "Installing required packages..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r requirements.txt
echo

echo "Creating .env file from template..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env file created! Edit it to configure your settings."
else
  echo ".env file already exists, skipping..."
fi
echo

echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo
echo "Next steps:"
echo "1. Edit .env to configure your cryptocurrency symbols"
echo "2. Run ./start_gui.sh for the GUI, or ./start_monitor.sh for console"
echo
