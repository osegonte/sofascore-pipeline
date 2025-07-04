#!/bin/bash
# Check Stage 7 dependencies on other stages

echo "🔍 Checking Stage 7 dependencies..."

# Check Stage 5 (Feature Engineering)
if [ -f "../demo_training_dataset.csv" ]; then
    echo "✅ Stage 5: Training data available"
else
    echo "⚠️  Stage 5: Training data missing (run feature generation)"
fi

# Check Stage 6 (ML Models)
if [ -d "../data/models/saved_models" ]; then
    model_count=$(ls ../data/models/saved_models/*.joblib 2>/dev/null | wc -l)
    if [ "$model_count" -gt 0 ]; then
        echo "✅ Stage 6: $model_count ML models available"
    else
        echo "⚠️  Stage 6: No trained models found"
    fi
else
    echo "⚠️  Stage 6: Models directory missing (run ML training)"
fi

# Check Python environment
if [ -f "../venv/bin/activate" ]; then
    echo "✅ Python virtual environment available"
else
    echo "⚠️  Python virtual environment missing"
fi

# Check core pipeline
if [ -f "../src/main.py" ]; then
    echo "✅ Core pipeline available"
else
    echo "⚠️  Core pipeline missing"
fi

echo ""
echo "💡 To ensure full functionality:"
echo "   1. Run Stage 5: python -m src.main demo-features"
echo "   2. Run Stage 6: python -m src.main train-ml"  
echo "   3. Start Stage 7: ./stage7_main.sh start"
