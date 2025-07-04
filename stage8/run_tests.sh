#!/bin/bash
# Run Stage 8 tests

echo "🧪 Running Stage 8 Tests"
echo "========================"

cd "$(dirname "$0")"
VENV_DIR="../venv"

if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
fi

python3 tests/test_integration.py
