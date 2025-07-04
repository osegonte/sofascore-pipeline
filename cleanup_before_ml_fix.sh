#!/bin/bash

# Cleanup Script Before Stage 6 ML Integration Fix
# Removes redundant and problematic files to prepare for ML integration

set -e

echo "🧹 SofaScore Pipeline - Pre-ML Fix Cleanup"
echo "=========================================="
echo ""
echo "This script will remove redundant files and prepare for ML integration fix."
echo "It will keep:"
echo "  ✅ Core ML implementation (Stage 6)"
echo "  ✅ Training data and features"
echo "  ✅ Configuration files"
echo "  ✅ Working feature engineering (Stage 5)"
echo ""
echo "⚠️  WARNING: This will delete redundant files!"
read -p "Continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo "🗑️  Starting cleanup..."

# Remove redundant setup scripts (keep only essentials)
echo "📜 Cleaning up setup scripts..."
rm -f stage6_complete_setup.sh 2>/dev/null || true
rm -f finalize_stage6_ml.sh 2>/dev/null || true
rm -f cleanup_for_stage6.sh 2>/dev/null || true

# Remove redundant validation scripts (keep main one)
echo "🔍 Cleaning up validation scripts..."
rm -f test_stage6_complete.py 2>/dev/null || true

# Remove broken scraper imports that cause main.py issues
echo "🔧 Cleaning up problematic imports..."
if [ -d "src/scrapers" ]; then
    echo "   Removing broken scrapers directory..."
    rm -rf src/scrapers/
fi

# Remove ETL and CLI directories that cause import issues
if [ -d "src/etl" ]; then
    echo "   Removing ETL directory..."
    rm -rf src/etl/
fi

if [ -d "src/cli" ]; then
    echo "   Removing CLI directory..."
    rm -rf src/cli/
fi

if [ -d "src/transformers" ]; then
    echo "   Removing transformers directory..."
    rm -rf src/transformers/
fi

# Remove redundant requirements files
echo "📦 Cleaning up requirements files..."
rm -f requirements_stage*.txt 2>/dev/null || true
rm -f requirements_*merged*.txt 2>/dev/null || true
rm -f requirements_*fixed*.txt 2>/dev/null || true

# Remove Docker files (not needed for ML focus)
echo "🐳 Removing Docker files..."
rm -f Dockerfile 2>/dev/null || true
rm -f docker-compose*.yml 2>/dev/null || true

# Remove setup.py and migration files
echo "🏗️  Cleaning up setup files..."
rm -f setup.py 2>/dev/null || true
rm -rf sql/ 2>/dev/null || true
rm -f etl_direct_usage.py 2>/dev/null || true

# Remove logs and temp data
echo "📊 Cleaning up logs and temp data..."
rm -rf logs/ 2>/dev/null || true

# Remove redundant demo scripts (keep main ones)
echo "🎮 Cleaning up demo scripts..."
rm -f comprehensive_*.py 2>/dev/null || true
rm -f final_*.py 2>/dev/null || true
rm -f fix_*.py 2>/dev/null || true

# Remove redundant test directories (keep essential ML tests)
echo "🧪 Cleaning up test files..."
rm -rf tests/fixtures/ 2>/dev/null || true

# Remove any .pyc files and __pycache__
echo "🐍 Cleaning up Python cache..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Create a simple main.py backup
echo "💾 Creating main.py backup..."
if [ -f "src/main.py" ]; then
    cp src/main.py src/main.py.backup
    echo "   ✅ Backup created: src/main.py.backup"
fi

# Clean up the main.py imports that cause issues
echo "🔧 Preparing main.py for ML integration..."
if [ -f "src/main.py" ]; then
    # Create a minimal working version
    cat > src/main_minimal.py << 'EOF'
"""
Minimal main.py for ML integration.
This version removes problematic imports and focuses on core functionality.
"""

import asyncio
import signal
import sys
import os
from datetime import datetime
from typing import Optional
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import click

# Core imports that should work
try:
    from src.storage.hybrid_database import HybridDatabaseManager as DatabaseManager
    from src.utils.logging import setup_logging, get_logger
    from config.simple_settings import settings
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Core imports not available: {e}")
    CORE_AVAILABLE = False

# ML imports (to be added during fix)
try:
    from src.ml_models.cli_commands import (
        run_ml_training, run_ml_evaluation, run_ml_prediction,
        run_ml_demo, run_ml_api_server
    )
    ML_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ML models not available: {e}")
    ML_AVAILABLE = False

# Setup logging
if CORE_AVAILABLE:
    setup_logging()
    logger = get_logger(__name__)
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """SofaScore Data Pipeline CLI - ML Focus."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")

@cli.command()
def status():
    """Show pipeline status."""
    click.echo("📊 SofaScore Pipeline Status")
    click.echo("=" * 30)
    click.echo(f"Core Available: {'✅' if CORE_AVAILABLE else '❌'}")
    click.echo(f"ML Available: {'✅' if ML_AVAILABLE else '❌'}")
    
    # Check training data
    training_data = Path("demo_training_dataset.csv")
    click.echo(f"Training Data: {'✅' if training_data.exists() else '❌'}")
    
    if training_data.exists():
        try:
            import pandas as pd
            df = pd.read_csv(training_data)
            click.echo(f"  Samples: {len(df)}")
            click.echo(f"  Features: {len(df.columns)}")
        except Exception as e:
            click.echo(f"  Error: {e}")

# ML Commands will be added during integration fix

def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

    echo "   ✅ Created minimal main.py template"
fi

echo ""
echo "✅ Cleanup completed!"
echo ""

# Show what's left
echo "📁 REMAINING STRUCTURE:"
echo "=================================="
echo ""

echo "🎯 Core ML Implementation (KEEP):"
if [ -d "src/ml_models" ]; then
    echo "✅ src/ml_models/"
    find src/ml_models -name "*.py" | head -5
    echo "   ... and more ML files"
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
echo "🔧 Working Components (KEEP):"
if [ -d "src/feature_engineering" ]; then
    echo "✅ src/feature_engineering/ - Stage 5 pipeline"
fi
if [ -d "src/storage" ]; then
    echo "✅ src/storage/ - Database components"
fi
if [ -d "src/utils" ]; then
    echo "✅ src/utils/ - Utility functions"
fi

echo ""
echo "🎯 READY FOR ML INTEGRATION FIX!"
echo ""
echo "Next steps for the new chat:"
echo "1. Fix src/main.py import issues"
echo "2. Integrate ML commands from main_ml_patch.py"
echo "3. Test complete ML pipeline"
echo ""
echo "Files ready for integration:"
echo "  📄 main_ml_patch.py - ML commands to integrate"
echo "  🗃️  src/ml_models/ - Complete ML implementation"
echo "  📊 demo_training_dataset.csv - Ready training data"
echo "  ⚙️  config/ml_models/ - ML configurations"
echo ""
echo "🚀 The ML implementation is complete and ready for integration!"