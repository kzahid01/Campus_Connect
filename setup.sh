#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Campus Connect — Quick Setup Script
# ─────────────────────────────────────────────────────────────

set -e

echo ""
echo "🎓  Campus Connect Setup"
echo "────────────────────────"

# 1. Create & activate virtual environment
if [ ! -d ".venv" ]; then
  echo "→ Creating virtual environment..."
  python3 -m venv .venv
fi

echo "→ Activating virtual environment..."
source .venv/bin/activate

# 2. Install dependencies
echo "→ Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 3. Run the app
echo ""
echo "✅  Setup complete!"
echo "    Starting Campus Connect at http://127.0.0.1:5000"
echo "    Press Ctrl+C to stop."
echo ""
python app.py
