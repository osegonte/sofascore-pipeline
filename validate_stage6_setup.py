#!/usr/bin/env python3
"""
Stage 6 Setup Validation Script

Validates that all Stage 6 components are properly installed and configured.
"""

import sys
from pathlib import Path
import importlib

def check_file_exists(file_path, description):
    """Check if a file exists and report status."""
    path = Path(file_path)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {file_path}")
    if exists and path.is_file():
        size = path.stat().st_size
        print(f"    Size: {size:,} bytes")
    return exists

def check_directory_exists(dir_path, description):
    """Check if a directory exists and report contents."""
    path = Path(dir_path)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {dir_path}")
    if exists and path.is_dir():
        files = list(path.iterdir())
        print(f"    Contents: {len(files)} items")
    return exists

def check_python_import(module_name, description):
    """Check if a Python module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - {e}")
        return False

def main():
    """Run complete Stage 6 validation."""
    print("🔍 Stage 6 ML Model Development - Setup Validation")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Check directory structure
    print("\n📁 Directory Structure:")
    directories = [
        ("src/ml_models", "ML Models Package"),
        ("src/ml_models/training", "Training Pipeline"),
        ("src/ml_models/evaluation", "Evaluation Framework"),
        ("src/ml_models/prediction", "Prediction API"),
        ("config/ml_models", "ML Configuration"),
        ("data/models", "Models Storage"),
        ("data/models/saved_models", "Saved Models"),
        ("data/models/evaluation", "Evaluation Results"),
        ("tests/ml_models", "ML Tests")
    ]
    
    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False
    
    # 2. Check core files
    print("\n📄 Core Files:")
    files = [
        ("src/ml_models/__init__.py", "ML Package Init"),
        ("src/ml_models/cli_commands.py", "CLI Commands"),
        ("config/ml_models/training_config.json", "Training Config"),
        ("config/ml_models/evaluation_config.json", "Evaluation Config"),
        ("config/ml_models/prediction_config.json", "Prediction Config"),
        ("requirements_ml.txt", "ML Requirements"),
        ("demo_stage6_ml.py", "Demo Script"),
        ("validate_stage6_setup.py", "Validation Script")
    ]
    
    for file_path, description in files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 3. Check training data
    print("\n📊 Training Data:")
    data_files = [
        ("demo_training_dataset.csv", "Main Training Dataset"),
        ("demo_features/match_12345_features.json", "Sample Features")
    ]
    
    for file_path, description in data_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Check training data content
    if Path("demo_training_dataset.csv").exists():
        try:
            import pandas as pd
            df = pd.read_csv("demo_training_dataset.csv")
            print(f"    Samples: {len(df)}")
            print(f"    Features: {len(df.columns)}")
            
            # Check target columns
            targets = ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']
            for target in targets:
                if target in df.columns:
                    positive_count = df[target].sum()
                    total_count = len(df)
                    print(f"    {target}: {positive_count}/{total_count} ({positive_count/total_count*100:.1f}% positive)")
                else:
                    print(f"    ❌ Missing target: {target}")
                    all_checks_passed = False
        except ImportError:
            print("    ⚠️  Cannot validate data content (pandas not available)")
        except Exception as e:
            print(f"    ❌ Error reading training data: {e}")
            all_checks_passed = False
    
    # 4. Check Python dependencies
    print("\n🐍 Python Dependencies:")
    dependencies = [
        ("pandas", "Data Processing"),
        ("numpy", "Numerical Computing"),
        ("scikit-learn", "Machine Learning"),
        ("matplotlib", "Plotting"),
        ("seaborn", "Statistical Visualization"),
        ("joblib", "Model Persistence"),
        ("click", "CLI Framework")
    ]
    
    for module, description in dependencies:
        if not check_python_import(module, description):
            all_checks_passed = False
    
    # Optional dependencies
    print("\n📦 Optional Dependencies:")
    optional_deps = [
        ("xgboost", "XGBoost Models"),
        ("fastapi", "API Framework"),
        ("uvicorn", "API Server"),
        ("plotly", "Interactive Plots"),
        ("optuna", "Hyperparameter Optimization")
    ]
    
    for module, description in optional_deps:
        check_python_import(module, description)
    
    # 5. Check ML module imports
    print("\n🤖 ML Module Imports:")
    try:
        from src.ml_models.cli_commands import MLCommandRunner
        print("✅ CLI Commands: MLCommandRunner")
    except ImportError as e:
        print(f"❌ CLI Commands: {e}")
        all_checks_passed = False
    
    # 6. Configuration validation
    print("\n⚙️  Configuration Validation:")
    config_files = [
        "config/ml_models/training_config.json",
        "config/ml_models/evaluation_config.json", 
        "config/ml_models/prediction_config.json"
    ]
    
    for config_file in config_files:
        try:
            import json
            with open(config_file) as f:
                config = json.load(f)
            print(f"✅ {Path(config_file).name}: Valid JSON")
        except FileNotFoundError:
            print(f"❌ {Path(config_file).name}: File not found")
            all_checks_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ {Path(config_file).name}: Invalid JSON - {e}")
            all_checks_passed = False
        except Exception as e:
            print(f"❌ {Path(config_file).name}: Error - {e}")
            all_checks_passed = False
    
    # 7. Final summary
    print("\n📋 Validation Summary:")
    print("=" * 30)
    
    if all_checks_passed:
        print("🎉 All checks passed! Stage 6 is ready for use.")
        print("\n🚀 Quick Start Commands:")
        print("   python demo_stage6_ml.py")
        print("   python -m src.main train-ml")
        print("   python -m src.main ml-status")
        return True
    else:
        print("❌ Some checks failed. Please address the issues above.")
        print("\n🔧 Common fixes:")
        print("   pip install -r requirements_ml.txt")
        print("   python src/feature_engineering/cli_commands.py  # Generate training data")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
