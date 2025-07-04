#!/usr/bin/env python3
"""
Validate Stage 6 ML setup and dependencies.
"""

import sys
import os
import json
from pathlib import Path

def validate_directories():
    """Validate required directories exist."""
    required_dirs = [
        'src/ml_models',
        'src/ml_models/training',
        'src/ml_models/evaluation', 
        'src/ml_models/prediction',
        'data/models/saved_models',
        'data/models/experiments',
        'config/ml_models',
        'logs/ml_models'
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

def validate_config_files():
    """Validate configuration files."""
    config_files = [
        'config/ml_models/model_config.json',
        'config/ml_models/experiment_config.json',
        'config/ml_models/logging_config.json'
    ]
    
    for config_file in config_files:
        if not Path(config_file).exists():
            print(f"❌ Missing config file: {config_file}")
            return False
        
        try:
            with open(config_file) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {config_file}: {e}")
            return False
    
    print("✅ All configuration files are valid")
    return True

def validate_dependencies():
    """Validate ML dependencies."""
    required_packages = [
        'sklearn', 'xgboost', 'pandas', 'numpy', 
        'matplotlib', 'seaborn', 'joblib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        print("Run: pip install -r requirements_stage6.txt")
        return False
    
    print("✅ All required packages available")
    return True

def validate_training_data():
    """Validate training data availability."""
    training_files = [
        'demo_training_dataset.csv',
        'demo_features/match_12345_features.json'
    ]
    
    available_files = []
    for file_path in training_files:
        if Path(file_path).exists():
            available_files.append(file_path)
    
    if not available_files:
        print("⚠️  No training data found")
        print("Run Stage 5 feature generation first")
        return False
    
    print(f"✅ Training data available: {available_files}")
    return True

def main():
    """Run all validations."""
    print("🔍 Validating Stage 6 ML Setup")
    print("=" * 40)
    
    all_valid = True
    all_valid &= validate_directories()
    all_valid &= validate_config_files()
    all_valid &= validate_dependencies()
    all_valid &= validate_training_data()
    
    print("\n" + "=" * 40)
    if all_valid:
        print("🎉 Stage 6 setup validation successful!")
        print("Ready to develop ML models.")
    else:
        print("❌ Stage 6 setup validation failed!")
        print("Please fix the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
