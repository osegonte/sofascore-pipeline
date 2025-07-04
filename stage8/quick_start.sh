#!/bin/bash
# Quick start for Stage 8 Development

echo "🚀 Stage 8 Quick Start"
echo "====================="
echo ""

# Go to project root
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

echo "1. Checking Stage 7 status..."
if [ -d "stage7/pids" ] && [ -n "$(ls -A stage7/pids 2>/dev/null)" ]; then
    echo "   ✅ Stage 7 is running"
else
    echo "   ⚠️  Stage 7 is not running"
    echo "   💡 Start with: ./stage7.sh start"
    echo ""
fi

echo "2. Starting Stage 8 dashboard..."
echo "   🌐 Dashboard: http://localhost:8008"
echo "   📚 API Docs: http://localhost:8008/docs"
echo ""

exec ./stage8.sh start
