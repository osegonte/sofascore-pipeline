#!/bin/bash
# Start Stage 8 Dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

echo "🚀 Starting Stage 8 Dashboard..."

# Check if Stage 7 is running
if [ ! -d "$PROJECT_ROOT/stage7/pids" ] || [ -z "$(ls -A "$PROJECT_ROOT/stage7/pids" 2>/dev/null)" ]; then
    echo "⚠️  Stage 7 doesn't appear to be running"
    echo "💡 Start Stage 7 first with: ./stage7.sh start"
    echo ""
fi

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Start the dashboard backend
echo "🌐 Starting dashboard server..."
echo "📊 Dashboard URL: http://localhost:8008"
echo "📚 API Documentation: http://localhost:8008/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m stage8.backend.app
