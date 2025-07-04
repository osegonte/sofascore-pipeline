#!/bin/bash
# Quick start script for Stage 7

echo "🚀 Stage 7 Quick Start"
echo "====================="

echo "1. Running dependency check..."
./check_dependencies.sh

echo ""
echo "2. Running tests..."
./tests/test_stage7.sh

echo ""
echo "3. Ready to start Stage 7!"
echo ""
echo "Options:"
echo "  ./stage7_main.sh start    # Start real-time analysis"
echo "  ./demo_stage7.sh          # Run demo"
echo "  ./stage7_main.sh status   # Check status"
echo ""
echo "📖 For more info, see README.md"
