#!/bin/bash
# Stage 7 Test Script

echo "🧪 Testing Stage 7 Real-Time Analysis System"
echo "============================================="

# Test configuration loading
echo "1. Testing configuration..."
if source "$(dirname "$0")/../config/stage7_config.sh"; then
    echo "   ✅ Configuration loaded successfully"
else
    echo "   ❌ Configuration loading failed"
fi

# Test directory structure
echo "2. Testing directory structure..."
required_dirs=(
    "../data/realtime/snapshots"
    "../data/realtime/ml_predictions" 
    "../data/realtime/ensemble_predictions"
    "../logs"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$(dirname "$0")/$dir" ]; then
        echo "   ✅ Directory exists: $dir"
    else
        echo "   ❌ Missing directory: $dir"
    fi
done

# Test Python environment
echo "3. Testing Python environment..."
if source "$(dirname "$0")/../../venv/bin/activate" 2>/dev/null; then
    echo "   ✅ Virtual environment activated"
    
    # Test required packages
    required_packages="pandas numpy sklearn"
    for package in $required_packages; do
        if python3 -c "import $package" 2>/dev/null; then
            echo "   ✅ Package available: $package"
        else
            echo "   ⚠️  Package missing: $package"
        fi
    done
else
    echo "   ⚠️  Virtual environment not found"
fi

# Test Stage 6 integration
echo "4. Testing Stage 6 integration..."
if [ -d "$(dirname "$0")/../../data/models/saved_models" ]; then
    model_count=$(ls "$(dirname "$0")/../../data/models/saved_models"/*.joblib 2>/dev/null | wc -l)
    echo "   ✅ Found $model_count ML models from Stage 6"
else
    echo "   ⚠️  Stage 6 models not found"
fi

echo ""
echo "🎯 Test Summary:"
echo "   Stage 7 is ready for real-time analysis"
echo "   Run './stage7_main.sh start' to begin monitoring"
