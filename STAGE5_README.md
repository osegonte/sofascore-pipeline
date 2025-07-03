# Stage 5: Feature Engineering Pipeline Setup

This directory contains the complete Stage 5 Feature Engineering Pipeline implementation.

## 📁 Directory Structure Created

```
src/feature_engineering/          # Main feature engineering package
data/features/                    # Individual match features
data/ml_datasets/                # ML-ready datasets
config/feature_engineering/      # Configuration files
logs/feature_engineering/        # Feature engineering logs
tests/feature_engineering/       # Tests for Stage 5
scripts/                         # Utility scripts
```

## ⚡ Quick Start

1. **Validate Setup**:
   ```bash
   python scripts/validate_stage5_setup.py
   ```

2. **Install Dependencies**:
   ```bash
   bash scripts/merge_requirements.sh
   pip install -r requirements.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/feature_engineering/
   ```

## 🔧 Configuration

Main configuration file: `config/feature_engineering/feature_config.json`

Key settings:
- `rolling_windows`: Time windows for rolling statistics
- `goal_prediction_windows`: Prediction horizons
- `feature_selection`: Feature filtering parameters
- `data_split`: Train/validation/test ratios

## 📝 Next Steps

1. Copy the Python implementation files to `src/feature_engineering/`
2. Update `src/main.py` with new CLI commands
3. Test with your Stage 4 normalized data

## 🆘 Troubleshooting

- **Permission errors**: Run `chmod +x scripts/*.sh`
- **Import errors**: Ensure all dependencies are installed
- **Configuration errors**: Validate JSON syntax in config files

## 📊 Expected Output

After setup:
- ✅ Directory structure created
- ✅ Configuration files ready
- ✅ Test framework set up
- ✅ Requirements defined
- ✅ Ready for Python module implementation
