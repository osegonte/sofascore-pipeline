#!/usr/bin/env python3
"""
Validate Stage 5 setup and dependencies.
"""

import sys
import os
import json
from pathlib import Path

def validate_directories():
    """Validate required directories exist."""
    required_dirs = [
        'src/feature_engineering',
        'data/features',
        'data/ml_datasets',
        'config/feature_engineering',
        'logs/feature_engineering'
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    print("✅ All required directories exist")
    return True

def validate_config():
    """Validate configuration files."""
    config_file = Path('config/feature_engineering/feature_config.json')
    
    if not config_file.exists():
        print("❌ Feature configuration file missing")
        return False
    
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        required_keys = [
            'rolling_windows', 'goal_prediction_windows', 
            'feature_selection', 'data_split'
        ]
        
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"❌ Missing configuration keys: {missing_keys}")
            return False
        
        print("✅ Configuration file is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration: {e}")
        return False

def validate_python_modules():
    """Validate Python modules can be imported."""
    try:
        # Test basic imports
        import numpy
        import pandas
        print("✅ Required Python packages available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        return False

def main():
    """Run all validations."""
    print("🔍 Validating Stage 5 Setup")
    print("=" * 30)
    
    all_valid = True
    all_valid &= validate_directories()
    all_valid &= validate_config()
    all_valid &= validate_python_modules()
    
    print("\n" + "=" * 30)
    if all_valid:
        print("🎉 Stage 5 setup validation successful!")
        print("Ready to create feature engineering modules.")
    else:
        print("❌ Stage 5 setup validation failed!")
        print("Please fix the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
