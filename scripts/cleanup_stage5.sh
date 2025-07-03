#!/bin/bash

# Cleanup script for Stage 5 setup (use with caution!)

echo "⚠️  WARNING: This will remove all Stage 5 setup files!"
echo "Are you sure you want to continue? (yes/no)"
read -r confirmation

if [ "$confirmation" = "yes" ]; then
    echo "🧹 Cleaning up Stage 5 files..."
    
    # Remove directories (be careful!)
    rm -rf src/feature_engineering
    rm -rf data/features
    rm -rf data/ml_datasets
    rm -rf config/feature_engineering
    rm -rf logs/feature_engineering
    rm -rf tests/feature_engineering
    
    # Remove files
    rm -f requirements_stage5.txt
    rm -f requirements_merged.txt
    rm -f STAGE5_README.md
    rm -f scripts/validate_stage5_setup.py
    rm -f scripts/merge_requirements.sh
    
    echo "✅ Stage 5 cleanup completed"
else
    echo "❌ Cleanup cancelled"
fi
