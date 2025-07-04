#!/bin/bash

# Stage 6: ML Model Development - Setup Script
# Creates directory structure, installs dependencies, and initializes ML pipeline

set -e

echo "🚀 Setting up Stage 6: ML Model Development"
echo "=" * 60

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "✅ Created directory: $1"
    else
        echo "📁 Directory exists: $1"
    fi
}

# Create Stage 6 directory structure
echo "📁 Creating Stage 6 directory structure..."

create_dir "src/ml_models"
create_dir "src/ml_models/training"
create_dir "src/ml_models/evaluation"
create_dir "src/ml_models/prediction"
create_dir "src/ml_models/utils"

create_dir "data/models"
create_dir "data/models/saved_models"
create_dir "data/models/experiments"
create_dir "data/models/predictions"

create_dir "config/ml_models"
create_dir "logs/ml_models"
create_dir "tests/ml_models"

create_dir "scripts/ml_models"
create_dir "notebooks"  # For analysis and experimentation

echo ""
echo "📝 Creating Stage 6 configuration files..."

# Create ML model configuration
cat > config/ml_models/model_config.json << 'EOF'
{
  "models": {
    "xgboost_classifier": {
      "type": "classification",
      "library": "xgboost",
      "hyperparameters": {
        "n_estimators": [100, 200, 300],
        "max_depth": [3, 6, 9],
        "learning_rate": [0.01, 0.1, 0.2],
        "subsample": [0.8, 0.9, 1.0],
        "colsample_bytree": [0.8, 0.9, 1.0],
        "random_state": 42
      },
      "cv_folds": 5,
      "scoring": "f1"
    },
    "random_forest": {
      "type": "classification",
      "library": "sklearn",
      "hyperparameters": {
        "n_estimators": [100, 200, 300],
        "max_depth": [5, 10, 15, null],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "random_state": 42
      },
      "cv_folds": 5,
      "scoring": "f1"
    },
    "logistic_regression": {
      "type": "classification",
      "library": "sklearn",
      "hyperparameters": {
        "C": [0.1, 1.0, 10.0],
        "penalty": ["l1", "l2"],
        "solver": ["liblinear", "lbfgs"],
        "random_state": 42,
        "max_iter": 1000
      },
      "cv_folds": 5,
      "scoring": "f1"
    }
  },
  "training": {
    "test_size": 0.2,
    "validation_size": 0.2,
    "random_state": 42,
    "stratify": true,
    "feature_selection": {
      "enabled": true,
      "method": "mutual_info",
      "k_best": 15,
      "variance_threshold": 0.01
    },
    "scaling": {
      "enabled": true,
      "method": "standard",
      "feature_exclude": ["match_id", "minute", "home_team_id", "away_team_id"]
    }
  },
  "targets": {
    "goal_next_1min_any": {
      "type": "binary",
      "threshold": 0.5,
      "priority": "high"
    },
    "goal_next_5min_any": {
      "type": "binary", 
      "threshold": 0.5,
      "priority": "medium"
    },
    "goal_next_15min_any": {
      "type": "binary",
      "threshold": 0.5,
      "priority": "low"
    }
  },
  "evaluation": {
    "metrics": ["accuracy", "precision", "recall", "f1", "auc", "log_loss"],
    "cross_validation": {
      "enabled": true,
      "folds": 5,
      "shuffle": true,
      "random_state": 42
    },
    "feature_importance": {
      "enabled": true,
      "plot": true,
      "top_n": 20
    }
  },
  "prediction": {
    "confidence_threshold": 0.6,
    "ensemble_voting": "soft",
    "calibration": {
      "enabled": true,
      "method": "isotonic"
    }
  }
}
EOF

# Create experiment tracking config
cat > config/ml_models/experiment_config.json << 'EOF'
{
  "experiment_tracking": {
    "enabled": true,
    "storage_path": "data/models/experiments",
    "auto_save": true,
    "version_models": true
  },
  "model_storage": {
    "base_path": "data/models/saved_models",
    "format": "joblib",
    "compression": true,
    "metadata_format": "json"
  },
  "performance_monitoring": {
    "enabled": true,
    "metrics_window": 1000,
    "drift_detection": {
      "enabled": true,
      "method": "ks_test",
      "threshold": 0.05
    },
    "retraining_triggers": {
      "performance_drop": 0.05,
      "data_drift": true,
      "time_based": "weekly"
    }
  },
  "api_config": {
    "host": "0.0.0.0",
    "port": 8001,
    "debug": false,
    "cors_enabled": true,
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 100
    }
  }
}
EOF

# Create logging configuration for ML models
cat > config/ml_models/logging_config.json << 'EOF'
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
    },
    "simple": {
      "format": "%(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "simple",
      "stream": "ext://sys.stdout"
    },
    "ml_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "detailed",
      "filename": "logs/ml_models/ml_pipeline.log",
      "maxBytes": 10485760,
      "backupCount": 5
    },
    "training_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "detailed",
      "filename": "logs/ml_models/training.log",
      "maxBytes": 10485760,
      "backupCount": 3
    },
    "prediction_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "INFO",
      "formatter": "detailed",
      "filename": "logs/ml_models/predictions.log",
      "maxBytes": 10485760,
      "backupCount": 3
    }
  },
  "loggers": {
    "ml_models": {
      "level": "DEBUG",
      "handlers": ["console", "ml_file"],
      "propagate": false
    },
    "ml_models.training": {
      "level": "DEBUG", 
      "handlers": ["console", "training_file"],
      "propagate": false
    },
    "ml_models.prediction": {
      "level": "INFO",
      "handlers": ["console", "prediction_file"],
      "propagate": false
    }
  },
  "root": {
    "level": "INFO",
    "handlers": ["console"]
  }
}
EOF

echo ""
echo "📦 Creating Stage 6 requirements..."

# Create ML-specific requirements
cat > requirements_stage6.txt << 'EOF'
# Stage 6: ML Model Development Requirements

# Core ML Libraries
scikit-learn>=1.3.2
xgboost>=2.0.0
lightgbm>=4.1.0

# Data Processing (already have pandas, numpy)
scipy>=1.11.0
joblib>=1.3.0

# Model Evaluation & Visualization
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.17.0
shap>=0.43.0

# Hyperparameter Optimization
optuna>=3.4.0
scikit-optimize>=0.9.0

# Model Monitoring & Drift Detection
evidently>=0.4.0
alibi-detect>=0.11.4

# API Framework
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.0

# Experiment Tracking
mlflow>=2.8.0

# Additional Utilities
tqdm>=4.66.0
cloudpickle>=3.0.0
EOF

# Create ML pipeline validation script
cat > scripts/ml_models/validate_stage6_setup.py << 'EOF'
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
EOF

chmod +x scripts/ml_models/validate_stage6_setup.py

echo ""
echo "🧪 Creating Stage 6 test files..."

# Create basic test file for ML models
cat > tests/ml_models/__init__.py << 'EOF'
"""
Tests for Stage 6 ML Model Development.
"""
EOF

cat > tests/ml_models/test_ml_basic.py << 'EOF'
#!/usr/bin/env python3
"""
Basic tests for Stage 6 ML pipeline.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestMLBasic(unittest.TestCase):
    """Basic ML pipeline tests."""
    
    def test_import_basic_packages(self):
        """Test that basic packages can be imported."""
        try:
            import numpy as np
            import pandas as pd
            import sklearn
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import basic packages: {e}")
    
    def test_config_files_exist(self):
        """Test that configuration files exist."""
        config_files = [
            'config/ml_models/model_config.json',
            'config/ml_models/experiment_config.json'
        ]
        
        for config_file in config_files:
            self.assertTrue(
                Path(config_file).exists(),
                f"Config file {config_file} does not exist"
            )
    
    def test_directories_exist(self):
        """Test that required directories exist."""
        required_dirs = [
            'src/ml_models',
            'data/models',
            'logs/ml_models'
        ]
        
        for directory in required_dirs:
            self.assertTrue(
                Path(directory).exists(),
                f"Directory {directory} does not exist"
            )

if __name__ == '__main__':
    unittest.main()
EOF

echo ""
echo "📄 Creating documentation..."

# Create Stage 6 README
cat > STAGE6_README.md << 'EOF'
# Stage 6: ML Model Development

This directory contains the complete Stage 6 ML Model Development implementation.

## 📁 Directory Structure Created

```
src/ml_models/                 # Main ML models package
├── training/                  # Model training modules
├── evaluation/                # Model evaluation tools
├── prediction/                # Real-time prediction API
└── utils/                     # ML utilities

data/models/                   # Model storage
├── saved_models/              # Trained model files
├── experiments/               # Experiment tracking
└── predictions/               # Prediction outputs

config/ml_models/              # ML configuration
└── *.json                     # Model and experiment configs

logs/ml_models/                # ML-specific logs
tests/ml_models/               # ML tests
scripts/ml_models/             # ML utility scripts
```

## ⚡ Quick Start

1. **Validate Setup**:
   ```bash
   python scripts/ml_models/validate_stage6_setup.py
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements_stage6.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/ml_models/
   ```

## 🔧 Configuration

Main configuration files:
- `config/ml_models/model_config.json`: Model hyperparameters and training settings
- `config/ml_models/experiment_config.json`: Experiment tracking and API settings
- `config/ml_models/logging_config.json`: Logging configuration

## 📝 Next Steps

1. Copy the Python implementation files to `src/ml_models/`
2. Update `src/main.py` with new CLI commands
3. Train models with your Stage 5 feature data
4. Deploy prediction API for real-time inference

## 🎯 Goals

- **Multi-Model Training**: XGBoost, Random Forest, Logistic Regression
- **Goal Prediction**: 1min, 5min, 15min prediction windows
- **Real-time API**: Fast prediction endpoint
- **Model Management**: Versioning, retraining, monitoring

## 📊 Expected Output

After full implementation:
- ✅ Trained ML models for goal prediction
- ✅ Model evaluation reports and metrics
- ✅ Real-time prediction API
- ✅ CLI commands for training and prediction
- ✅ Model monitoring and retraining pipeline
EOF

# Create requirements merger script
cat > scripts/ml_models/merge_requirements.sh << 'EOF'
#!/bin/bash

# Merge Stage 6 requirements with existing requirements

echo "🔗 Merging Stage 6 ML requirements with existing requirements.txt"

if [ -f "requirements.txt" ]; then
    echo "# Original requirements" > requirements_stage6_merged.txt
    cat requirements.txt >> requirements_stage6_merged.txt
    echo "" >> requirements_stage6_merged.txt
    echo "# Stage 6: ML Model Development Requirements" >> requirements_stage6_merged.txt
    cat requirements_stage6.txt >> requirements_stage6_merged.txt
    
    echo "✅ Merged requirements saved to requirements_stage6_merged.txt"
    echo "📝 Review the merged file and update requirements.txt manually"
else
    cp requirements_stage6.txt requirements.txt
    echo "✅ Created new requirements.txt with Stage 6 dependencies"
fi
EOF

chmod +x scripts/ml_models/merge_requirements.sh

# Create cleanup script
cat > scripts/ml_models/cleanup_stage6.sh << 'EOF'
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
EOF

chmod +x scripts/ml_models/cleanup_stage6.sh

echo ""
echo "✅ Stage 6 setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Install dependencies: bash scripts/ml_models/merge_requirements.sh && pip install -r requirements_stage6_merged.txt"
echo "2. Validate setup: python scripts/ml_models/validate_stage6_setup.py"
echo "3. Run tests: python -m pytest tests/ml_models/"
echo ""
echo "🎯 Ready for ML model implementation!"
echo "Check STAGE6_README.md for detailed usage instructions."