#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if ! python -c "import tkinter" 2>/dev/null; then
  echo "AVISO: tkinter não encontrado. No Debian/Ubuntu instale:"
  echo "  sudo apt install python3-tk"
fi

echo "Pronto. Ative o venv e rode: python app.py"
echo "  source .venv/bin/activate"
