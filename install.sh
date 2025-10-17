#!/usr/bin/env bash
set -e

echo "== KI-Scanner: Bootstrap script =="

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment 'venv'..."
  python3 -m venv venv
else
  echo "Virtual environment 'venv' already exists."
fi

# Activate venv
# shellcheck disable=SC1091
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt

echo "Bootstrap complete. Activate venv with: source venv/bin/activate"
