#!/bin/bash

# Cleanup script for Stage 6 setup (use with caution!)

echo "⚠️  WARNING: This will remove all Stage 6 setup files!"
echo "Are you sure you want to continue? (yes/no)"
read -r confirmation

if [ "$confirmation" = "yes" ]; then
    echo "🧹 Cleaning up Stage 6 files..."
    
    # Remove directories (be careful!)
    rm -rf src/ml_models
    rm -rf data/models
    rm -rf config/ml_models
    rm -rf logs/ml_models
    rm -rf tests/ml_models
    rm -rf scripts/ml_models
    
    # Remove files
    rm -f requirements_stage6.txt
    rm -f requirements_stage6_merged.txt
    rm -f STAGE6_README.md
    
    echo "✅ Stage 6 cleanup completed"
else
    echo "❌ Cleanup cancelled"
fi
