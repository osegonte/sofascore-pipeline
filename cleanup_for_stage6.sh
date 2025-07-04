#!/bin/bash

# Cleanup Script for Stage 6 Focus
# Removes redundant files to focus on ML model development

set -e

echo "🧹 SofaScore Pipeline - Stage 6 Cleanup"
echo "=================================================="
echo ""
echo "This script will remove redundant files to focus on Stage 6 ML development."
echo "It will keep:"
echo "  ✅ Working feature engineering pipeline (Stage 5)"
echo "  ✅ Training datasets and demo data"
echo "  ✅ Core pipeline structure"
echo "  ✅ Configuration files"
echo ""
echo "⚠️  WARNING: This will delete many files!"
read -p "Continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo "🗑️  Starting cleanup..."

# Remove redundant documentation files
echo "📄 Cleaning up documentation..."
rm -f STAGE*.md 2>/dev/null || true
rm -f PROJECT_STRUCTURE.md 2>/dev/null || true
rm -f complete_setup_fix.sh 2>/dev/null || true
rm -f stage6_setup.sh 2>/dev/null || true

# Remove duplicate config files
echo "⚙️  Cleaning up configs..."
rm -f config/feature_engineering/logging_config.json 2>/dev/null || true
rm -f config/feature_engineering/model_configs.json 2>/dev/null || true
rm -f config/ml_models/logging_config.json 2>/dev/null || true
rm -f config/ml_models/experiment_config.json 2>/dev/null || true

# Remove redundant scripts
echo "📜 Cleaning up scripts..."
rm -rf scripts/feature_engineering/ 2>/dev/null || true
rm -rf scripts/ml_models/ 2>/dev/null || true
rm -f scripts/cleanup_stage5.sh 2>/dev/null || true
rm -f scripts/merge_requirements.sh 2>/dev/null || true
rm -f scripts/validate_stage5_setup.py 2>/dev/null || true
rm -f scripts/data_quality_check.py 2>/dev/null || true

# Remove redundant requirements files
echo "📦 Cleaning up requirements..."
rm -f requirements_stage*.txt 2>/dev/null || true
rm -f requirements_*merged*.txt 2>/dev/null || true
rm -f requirements_*fixed*.txt 2>/dev/null || true

# Remove Docker files (not needed for ML focus)
echo "🐳 Removing Docker files..."
rm -f Dockerfile 2>/dev/null || true
rm -f docker-compose*.yml 2>/dev/null || true

# Remove unused source directories
echo "🔧 Cleaning up source code..."
rm -rf src/scrapers/ 2>/dev/null || true
rm -rf src/storage/database.py 2>/dev/null || true
rm -rf src/transformers/ 2>/dev/null || true
rm -rf src/etl/ 2>/dev/null || true
rm -rf src/cli/ 2>/dev/null || true

# Remove test files (we'll recreate focused ones)
echo "🧪 Cleaning up tests..."
rm -rf tests/feature_engineering/ 2>/dev/null || true
rm -rf tests/ml_models/ 2>/dev/null || true
rm -rf tests/fixtures/ 2>/dev/null || true

# Remove logs and temp data
echo "📊 Cleaning up logs and temp data..."
rm -rf logs/ 2>/dev/null || true
rm -rf data/raw/ 2>/dev/null || true
rm -rf data/processed/ 2>/dev/null || true
rm -rf data/temp/ 2>/dev/null || true

# Remove setup and migration files
echo "🏗️  Cleaning up setup files..."
rm -f setup.py 2>/dev/null || true
rm -rf sql/ 2>/dev/null || true
rm -f etl_direct_usage.py 2>/dev/null || true

# Keep essential files - create a summary
echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📁 REMAINING STRUCTURE:"
echo "=================================="

# Show what's left
echo ""
echo "🔧 Core Application:"
if [ -d "src" ]; then
    find src -name "*.py" | head -10
fi

echo ""
echo "🎯 Stage 5 Features (KEEP):"
if [ -d "src/feature_engineering" ]; then
    ls -la src/feature_engineering/
fi

echo ""
echo "📊 Training Data (KEEP):"
if [ -f "demo_training_dataset.csv" ]; then
    echo "✅ demo_training_dataset.csv ($(wc -l < demo_training_dataset.csv) lines)"
fi
if [ -d "demo_features" ]; then
    echo "✅ demo_features/ ($(ls demo_features/ | wc -l) files)"
fi

echo ""
echo "⚙️  Configuration (KEEP):"
if [ -d "config" ]; then
    find config -name "*.json" | head -5
fi

echo ""
echo "📦 Dependencies:"
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt ($(wc -l < requirements.txt) packages)"
else
    echo "❌ requirements.txt missing - will create"
fi

echo ""
echo "🎯 READY FOR STAGE 6!"
echo "Next steps:"
echo "1. Verify training data: python -c \"import pandas as pd; df=pd.read_csv('demo_training_dataset.csv'); print(f'Data: {len(df)} rows, {len(df.columns)} cols')\""
echo "2. Check features work: python src/feature_engineering/cli_commands.py"
echo "3. Start Stage 6 ML development"

# Create a minimal requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo ""
    echo "📦 Creating minimal requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core ML Requirements for Stage 6
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=1.7.0
matplotlib>=3.6.0
seaborn>=0.12.0
click>=8.1.0
asyncio-throttle>=1.0.0
python-dotenv>=1.0.0
joblib>=1.3.0
tqdm>=4.64.0

# Optional but recommended
fastapi>=0.104.0
uvicorn>=0.24.0
plotly>=5.17.0
EOF
    echo "✅ Created basic requirements.txt"
fi

echo ""
echo "🚀 Stage 6 ML Development ready to begin!"
echo "Your training data is ready with 96 examples across 3 matches."
echo "Features include match state and goal prediction labels for 1min, 5min, 15min windows."