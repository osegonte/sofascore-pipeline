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
