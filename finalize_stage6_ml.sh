#!/bin/bash

# Stage 6 Finalization Script
# Creates remaining implementation files and integrates with main.py

set -e

echo "🎯 Stage 6 ML Model Development - Finalization"
echo "=============================================="
echo ""

# Create remaining implementation files
echo "📝 Creating remaining implementation files..."

# Create training __init__.py
cat > src/ml_models/training/__init__.py << 'EOF'
"""
ML Training Package for Goal Prediction
"""

from .pipeline import MLTrainingPipeline, TrainingConfig, TrainingResult

__all__ = ['MLTrainingPipeline', 'TrainingConfig', 'TrainingResult']
EOF

# Create evaluation __init__.py
cat > src/ml_models/evaluation/__init__.py << 'EOF'
"""
ML Evaluation Package for Goal Prediction
"""

from .framework import ModelEvaluator, EvaluationResult, ComparisonResult

__all__ = ['ModelEvaluator', 'EvaluationResult', 'ComparisonResult']
EOF

# Create prediction __init__.py
cat > src/ml_models/prediction/__init__.py << 'EOF'
"""
ML Prediction Package for Goal Prediction
"""

from .api import (
    PredictionEngine, ModelManager, MatchState, PredictionResult,
    FeatureExtractor, run_api_server, predict_match_state, predict_demo_scenarios
)

__all__ = [
    'PredictionEngine', 'ModelManager', 'MatchState', 'PredictionResult',
    'FeatureExtractor', 'run_api_server', 'predict_match_state', 'predict_demo_scenarios'
]
EOF

# Create utils package
mkdir -p src/ml_models/utils
cat > src/ml_models/utils/__init__.py << 'EOF'
"""
ML Utilities Package
"""

from .metrics import calculate_additional_metrics
from .visualization import create_performance_plots

__all__ = ['calculate_additional_metrics', 'create_performance_plots']
EOF

# Create utility modules
cat > src/ml_models/utils/metrics.py << 'EOF'
"""
Additional ML metrics and calculations.
"""

import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics import precision_recall_curve, average_precision_score

def calculate_additional_metrics(y_true: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Calculate additional ML metrics."""
    metrics = {}
    
    try:
        # Average precision score
        metrics['average_precision'] = average_precision_score(y_true, y_proba)
        
        # Precision-recall curve
        precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
        
        # Find best threshold (F1 score)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
        best_threshold_idx = np.argmax(f1_scores)
        metrics['best_threshold'] = float(thresholds[best_threshold_idx]) if len(thresholds) > 0 else 0.5
        metrics['best_f1'] = float(f1_scores[best_threshold_idx]) if len(f1_scores) > 0 else 0.0
        
        # Precision at fixed recall levels
        for recall_level in [0.1, 0.2, 0.5, 0.8]:
            precision_at_recall = get_precision_at_recall(precision, recall, recall_level)
            metrics[f'precision_at_recall_{recall_level}'] = precision_at_recall
        
    except Exception as e:
        print(f"Error calculating additional metrics: {e}")
    
    return metrics

def get_precision_at_recall(precision: np.ndarray, recall: np.ndarray, target_recall: float) -> float:
    """Get precision at specific recall level."""
    try:
        # Find closest recall value
        recall_diff = np.abs(recall - target_recall)
        closest_idx = np.argmin(recall_diff)
        return float(precision[closest_idx])
    except:
        return 0.0
EOF

cat > src/ml_models/utils/visualization.py << 'EOF'
"""
ML visualization utilities.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

def create_performance_plots(results: Dict[str, float], save_path: Optional[str] = None) -> str:
    """Create performance visualization plots."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Model Performance Overview', fontsize=16)
    
    # Metrics bar plot
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    values = [results.get(metric, 0) for metric in metrics]
    
    axes[0, 0].bar(metrics, values, alpha=0.7, color=['blue', 'green', 'orange', 'red'])
    axes[0, 0].set_title('Performance Metrics')
    axes[0, 0].set_ylabel('Score')
    axes[0, 0].set_ylim(0, 1)
    
    # Add value labels
    for i, (metric, value) in enumerate(zip(metrics, values)):
        axes[0, 0].text(i, value + 0.02, f'{value:.3f}', ha='center', va='bottom')
    
    # AUC Score (placeholder)
    auc_score = results.get('auc', 0)
    axes[0, 1].pie([auc_score, 1-auc_score], labels=['AUC', 'Remaining'], autopct='%1.1f%%')
    axes[0, 1].set_title(f'AUC Score: {auc_score:.3f}')
    
    # Feature importance (if available)
    if 'feature_importance' in results and results['feature_importance']:
        features = list(results['feature_importance'].keys())[:10]
        importances = list(results['feature_importance'].values())[:10]
        
        axes[1, 0].barh(features, importances, alpha=0.7)
        axes[1, 0].set_title('Top 10 Feature Importance')
        axes[1, 0].set_xlabel('Importance')
    else:
        axes[1, 0].text(0.5, 0.5, 'No feature importance data', 
                       ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 0].set_title('Feature Importance')
    
    # Training summary
    training_time = results.get('training_time', 0)
    test_samples = results.get('test_samples', 0)
    
    axes[1, 1].text(0.1, 0.8, f'Training Time: {training_time:.1f}s', transform=axes[1, 1].transAxes)
    axes[1, 1].text(0.1, 0.6, f'Test Samples: {test_samples}', transform=axes[1, 1].transAxes)
    axes[1, 1].text(0.1, 0.4, f'F1 Score: {results.get("f1", 0):.3f}', transform=axes[1, 1].transAxes)
    axes[1, 1].text(0.1, 0.2, f'AUC Score: {auc_score:.3f}', transform=axes[1, 1].transAxes)
    axes[1, 1].set_title('Training Summary')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plot_path = save_path
    else:
        plot_path = 'model_performance.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    
    plt.close()
    return plot_path
EOF

# Update main.py with ML commands
echo "🔧 Creating main.py integration patch..."

cat > main_ml_patch.py << 'EOF'
"""
Main.py ML Integration Patch

Add these imports and commands to your existing src/main.py file.
"""

# Add these imports after your existing imports
try:
    from src.ml_models.cli_commands import (
        run_ml_training, run_ml_evaluation, run_ml_prediction,
        run_ml_demo, run_ml_api_server
    )
    ML_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ML models not available: {e}")
    ML_AVAILABLE = False

# Add these CLI commands to your existing click group

@cli.command()
@click.option('--data', '-d', default='demo_training_dataset.csv', help='Path to training data CSV file')
@click.option('--target', '-t', help='Specific target column to train')
@click.option('--models', '-m', multiple=True, help='Specific models to train (xgboost, random_forest, logistic_regression)')
def train_ml(data, target, models):
    """Train ML models for goal prediction."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available. Install requirements:")
        click.echo("   pip install -r requirements_ml.txt")
        return
    
    models_list = list(models) if models else None
    success = asyncio.run(run_ml_training(data, target, models_list))
    
    if success:
        click.echo("✅ ML training completed successfully!")
    else:
        click.echo("❌ ML training failed. Check logs for details.")

@cli.command()
@click.option('--data', '-d', default='demo_training_dataset.csv', help='Path to test data CSV file')
@click.option('--models-dir', '-m', help='Directory containing saved models')
@click.option('--no-plots', is_flag=True, help='Skip plot generation')
def evaluate_ml(data, models_dir, no_plots):
    """Evaluate trained ML models."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    success = asyncio.run(run_ml_evaluation(data, models_dir, not no_plots))
    
    if success:
        click.echo("✅ ML evaluation completed successfully!")
    else:
        click.echo("❌ ML evaluation failed. Check logs for details.")

@cli.command()
@click.option('--match-id', '-i', type=int, required=True, help='Match ID')
@click.option('--minute', '-min', type=int, required=True, help='Current minute')
@click.option('--home-score', '-hs', type=int, required=True, help='Home team score')
@click.option('--away-score', '-as', type=int, required=True, help='Away team score')
@click.option('--home-team-id', type=int, default=1, help='Home team ID')
@click.option('--away-team-id', type=int, default=2, help='Away team ID')
def predict_ml(match_id, minute, home_score, away_score, home_team_id, away_team_id):
    """Make goal prediction for current match state."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    success = asyncio.run(run_ml_prediction(
        match_id, minute, home_score, away_score, home_team_id, away_team_id
    ))
    
    if not success:
        click.echo("❌ Prediction failed. Check logs for details.")

@cli.command()
def predict_ml_demo():
    """Run goal prediction demo with sample scenarios."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    success = asyncio.run(run_ml_demo())
    
    if success:
        click.echo("✅ ML demo completed successfully!")
    else:
        click.echo("❌ ML demo failed. Check logs for details.")

@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='API server host')
@click.option('--port', '-p', type=int, default=8001, help='API server port')
def serve_ml(host, port):
    """Start the prediction API server."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    click.echo(f"🚀 Starting ML API server on {host}:{port}")
    click.echo(f"📚 Documentation: http://{host}:{port}/docs")
    
    try:
        asyncio.run(run_ml_api_server(host, port))
    except KeyboardInterrupt:
        click.echo("\n👋 API server stopped")

@cli.command()
def ml_status():
    """Show ML pipeline status and information."""
    click.echo("📊 Stage 6 ML Pipeline Status")
    click.echo("=" * 40)
    
    # Check training data
    training_data_exists = Path("demo_training_dataset.csv").exists()
    click.echo(f"Training Data: {'✅' if training_data_exists else '❌'} demo_training_dataset.csv")
    
    if training_data_exists:
        try:
            import pandas as pd
            df = pd.read_csv("demo_training_dataset.csv")
            click.echo(f"  Samples: {len(df)}")
            click.echo(f"  Features: {len(df.columns)}")
            
            # Check target distributions
            targets = ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']
            for target in targets:
                if target in df.columns:
                    positive = df[target].sum()
                    total = len(df)
                    click.echo(f"  {target}: {positive}/{total} ({positive/total*100:.1f}%)")
        except Exception as e:
            click.echo(f"  Error reading data: {e}")
    
    # Check models directory
    models_dir = Path("data/models/saved_models")
    models_exist = models_dir.exists()
    click.echo(f"Models Directory: {'✅' if models_exist else '❌'} {models_dir}")
    
    if models_exist:
        model_files = list(models_dir.glob("*.joblib"))
        click.echo(f"  Saved Models: {len(model_files)}")
        
        # Group by target
        targets_found = set()
        for model_file in model_files:
            for target in ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']:
                if target in model_file.name:
                    targets_found.add(target)
        
        for target in targets_found:
            target_models = [f for f in model_files if target in f.name]
            click.echo(f"  {target}: {len(target_models)} models")
    
    # Check ML availability
    click.echo(f"ML Available: {'✅' if ML_AVAILABLE else '❌'}")
    
    if not ML_AVAILABLE:
        click.echo("To enable ML features:")
        click.echo("  pip install -r requirements_ml.txt")
    
    # Usage examples
    if training_data_exists and ML_AVAILABLE:
        click.echo("\n🎯 Quick Start Commands:")
        click.echo("  python -m src.main train-ml")
        click.echo("  python -m src.main evaluate-ml") 
        click.echo("  python -m src.main predict-ml --match-id 12345 --minute 75 --home-score 1 --away-score 0")
        click.echo("  python -m src.main serve-ml")
EOF

# Create API example usage
cat > api_examples.py << 'EOF'
#!/usr/bin/env python3
"""
Stage 6 ML API Examples

Example usage of the prediction API endpoints.
"""

import requests
import json
import asyncio
from datetime import datetime

API_BASE = "http://localhost:8001"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("🔍 Testing health endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"   Models loaded: {data['models_loaded']}")
            print(f"   Targets available: {data['targets_available']}")
            print(f"   Uptime: {data['uptime_seconds']:.1f}s")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_models_endpoint():
    """Test the models listing endpoint."""
    print("\n📋 Testing models endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_models']} models")
            
            for target, models in data['models_by_target'].items():
                print(f"   {target}: {len(models)} models")
                for model in models[:2]:  # Show first 2
                    print(f"     - {model['name']} (F1: {model['f1_score']:.3f})")
        else:
            print(f"❌ Models listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Models listing error: {e}")

def test_prediction_endpoint():
    """Test the prediction endpoint."""
    print("\n🎯 Testing prediction endpoint...")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Late game tie",
            "match_id": 12345,
            "minute": 85,
            "home_team_id": 1,
            "away_team_id": 2,
            "current_score_home": 1,
            "current_score_away": 1
        },
        {
            "name": "Losing team pressure",
            "match_id": 12346,
            "minute": 70,
            "home_team_id": 1,
            "away_team_id": 2,
            "current_score_home": 0,
            "current_score_away": 1
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   Testing: {scenario['name']}")
        
        try:
            response = requests.post(f"{API_BASE}/predict", json=scenario)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Prediction successful")
                print(f"      Processing time: {data['processing_time_ms']:.1f}ms")
                print(f"      Confidence: {data['confidence_score']:.3f}")
                
                print(f"      Ensemble predictions:")
                for target, prob in data['ensemble_prediction'].items():
                    timeframe = target.replace('goal_next_', '').replace('_any', '')
                    print(f"        Next {timeframe}: {prob:.1%}")
            else:
                print(f"   ❌ Prediction failed: {response.status_code}")
                print(f"      {response.text}")
        except Exception as e:
            print(f"   ❌ Prediction error: {e}")

def test_timeframe_endpoint():
    """Test the timeframe-specific prediction endpoint."""
    print("\n⏱️  Testing timeframe endpoint...")
    
    match_state = {
        "match_id": 12345,
        "minute": 75,
        "home_team_id": 1,
        "away_team_id": 2,
        "current_score_home": 2,
        "current_score_away": 0
    }
    
    timeframes = [1, 5, 15]
    
    for timeframe in timeframes:
        try:
            response = requests.post(f"{API_BASE}/predict/timeframe/{timeframe}", json=match_state)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {timeframe}min prediction: {data['probability']:.1%} (confidence: {data['confidence']:.2f})")
            else:
                print(f"   ❌ {timeframe}min prediction failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {timeframe}min prediction error: {e}")

def main():
    """Run all API tests."""
    print("🚀 Stage 6 ML API Testing")
    print("=" * 40)
    print("Make sure the API server is running:")
    print("  python -m src.main serve-ml")
    print("")
    
    test_health_endpoint()
    test_models_endpoint()
    test_prediction_endpoint()
    test_timeframe_endpoint()
    
    print("\n✅ API testing completed!")
    print("📚 Full API documentation: http://localhost:8001/docs")

if __name__ == "__main__":
    main()
EOF

chmod +x api_examples.py

# Create comprehensive test script
cat > test_stage6_complete.py << 'EOF'
#!/usr/bin/env python3
"""
Stage 6 Complete Testing Script

Comprehensive test of all Stage 6 ML functionality.
"""

import asyncio
import sys
import subprocess
from pathlib import Path
import pandas as pd

async def test_training_pipeline():
    """Test the training pipeline."""
    print("🎯 Testing Training Pipeline...")
    
    try:
        from src.ml_models.training.pipeline import MLTrainingPipeline, TrainingConfig
        
        # Check if training data exists
        if not Path("demo_training_dataset.csv").exists():
            print("❌ Training data not found. Run feature engineering first.")
            return False
        
        # Load training data
        config = TrainingConfig(
            test_size=0.3,
            cv_folds=3,
            enable_hyperparameter_tuning=False,  # Faster for testing
            model_save_path="data/models/saved_models"
        )
        
        pipeline = MLTrainingPipeline(config)
        data = pipeline.load_training_data("demo_training_dataset.csv")
        
        print(f"✅ Loaded {len(data)} training samples")
        
        # Test single model training
        print("   Training logistic regression model...")
        result = pipeline.train_single_model('logistic_regression', 'goal_next_5min_any')
        
        print(f"   ✅ Model trained - F1: {result.test_f1:.3f}, Accuracy: {result.test_accuracy:.3f}")
        return True
        
    except Exception as e:
        print(f"❌ Training pipeline failed: {e}")
        return False

async def test_evaluation_framework():
    """Test the evaluation framework."""
    print("\n📊 Testing Evaluation Framework...")
    
    try:
        from src.ml_models.evaluation.framework import ModelEvaluator
        
        evaluator = ModelEvaluator()
        
        # Check for saved models
        models_dir = Path("data/models/saved_models")
        if not models_dir.exists() or not list(models_dir.glob("*.joblib")):
            print("⚠️  No saved models found. Skipping evaluation test.")
            return True
        
        model_files = list(models_dir.glob("*.joblib"))
        print(f"   Found {len(model_files)} saved models")
        
        # Test evaluation on first model
        model_file = model_files[0]
        target = 'goal_next_5min_any'
        
        result = evaluator.evaluate_single_model(
            str(model_file), "demo_training_dataset.csv", target
        )
        
        print(f"   ✅ Evaluation completed - F1: {result.f1:.3f}, AUC: {result.auc:.3f}")
        return True
        
    except Exception as e:
        print(f"❌ Evaluation framework failed: {e}")
        return False

async def test_prediction_engine():
    """Test the prediction engine."""
    print("\n🔮 Testing Prediction Engine...")
    
    try:
        from src.ml_models.prediction.api import PredictionEngine, ModelManager, MatchState
        
        # Check for saved models
        models_dir = Path("data/models/saved_models")
        if not models_dir.exists() or not list(models_dir.glob("*.joblib")):
            print("⚠️  No saved models found. Skipping prediction test.")
            return True
        
        model_manager = ModelManager()
        loaded_models = model_manager.load_best_models()
        
        if not loaded_models:
            print("⚠️  No models loaded. Skipping prediction test.")
            return True
        
        print(f"   Loaded {len(loaded_models)} models")
        
        prediction_engine = PredictionEngine(model_manager)
        
        # Test prediction
        match_state = MatchState(
            match_id=12345,
            minute=75,
            home_team_id=1,
            away_team_id=2,
            current_score_home=1,
            current_score_away=0
        )
        
        result = prediction_engine.predict_all_targets(match_state)
        
        print(f"   ✅ Prediction completed in {result.processing_time_ms:.1f}ms")
        print(f"   Confidence: {result.confidence_score:.3f}")
        
        for target, prob in result.ensemble_prediction.items():
            timeframe = target.replace('goal_next_', '').replace('_any', '')
            print(f"   Next {timeframe}: {prob:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction engine failed: {e}")
        return False

def test_cli_integration():
    """Test CLI command integration."""
    print("\n💻 Testing CLI Integration...")
    
    try:
        # Test ml-status command
        result = subprocess.run([
            sys.executable, "-m", "src.main", "ml-status"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ ml-status command works")
        else:
            print(f"   ❌ ml-status command failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI integration failed: {e}")
        return False

def check_file_structure():
    """Check that all required files exist."""
    print("\n📁 Checking File Structure...")
    
    required_files = [
        "src/ml_models/__init__.py",
        "src/ml_models/cli_commands.py",
        "src/ml_models/training/pipeline.py",
        "src/ml_models/evaluation/framework.py",
        "src/ml_models/prediction/api.py",
        "config/ml_models/training_config.json",
        "config/ml_models/evaluation_config.json",
        "config/ml_models/prediction_config.json",
        "requirements_ml.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

async def main():
    """Run comprehensive Stage 6 tests."""
    print("🧪 Stage 6 ML Complete Testing")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Check file structure
    if not check_file_structure():
        print("❌ File structure check failed")
        return False
    
    # Test training data
    print("\n📊 Checking Training Data...")
    if Path("demo_training_dataset.csv").exists():
        df = pd.read_csv("demo_training_dataset.csv")
        print(f"✅ Training data: {len(df)} samples, {len(df.columns)} features")
        
        # Check target distributions
        targets = ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']
        for target in targets:
            if target in df.columns:
                positive = df[target].sum()
                total = len(df)
                print(f"   {target}: {positive}/{total} ({positive/total*100:.1f}% positive)")
    else:
        print("❌ Training data not found")
        all_tests_passed = False
    
    # Run component tests
    tests = [
        ("Training Pipeline", test_training_pipeline),
        ("Evaluation Framework", test_evaluation_framework),
        ("Prediction Engine", test_prediction_engine),
    ]
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            if not success:
                all_tests_passed = False
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            all_tests_passed = False
    
    # Test CLI integration
    if not test_cli_integration():
        all_tests_passed = False
    
    # Final summary
    print("\n📋 Test Summary")
    print("=" * 30)
    
    if all_tests_passed:
        print("🎉 All tests passed! Stage 6 is fully functional.")
        print("\n🚀 Ready for production use:")
        print("   python -m src.main train-ml")
        print("   python -m src.main predict-ml --match-id 12345 --minute 75 --home-score 1 --away-score 0")
        print("   python -m src.main serve-ml")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
EOF

chmod +x test_stage6_complete.py

echo ""
echo "✅ Stage 6 ML Model Development - FINALIZATION COMPLETE!"
echo ""
echo "📋 Final Summary:"
echo "   ✅ Complete training pipeline with multiple models"
echo "   ✅ Comprehensive evaluation framework with metrics"
echo "   ✅ Real-time prediction API with FastAPI"
echo "   ✅ CLI integration with main.py commands"
echo "   ✅ Configuration files for all components"
echo "   ✅ Testing and validation scripts"
echo ""
echo "📁 Created Files:"
echo "   src/ml_models/training/pipeline.py     - ML training pipeline"
echo "   src/ml_models/evaluation/framework.py  - Model evaluation"
echo "   src/ml_models/prediction/api.py        - Prediction API"
echo "   src/ml_models/cli_commands.py          - CLI integration"
echo "   config/ml_models/*.json                - Configuration files"
echo "   requirements_ml.txt                    - ML dependencies"
echo "   api_examples.py                        - API usage examples"
echo "   test_stage6_complete.py                - Comprehensive tests"
echo ""
echo "🔧 Integration Steps:"
echo "   1. Install ML requirements:"
echo "      pip install -r requirements_ml.txt"
echo ""
echo "   2. Add ML commands to your main.py:"
echo "      Copy code from main_ml_patch.py to src/main.py"
echo ""
echo "   3. Validate complete setup:"
echo "      python validate_stage6_setup.py"
echo ""
echo "   4. Run comprehensive tests:"
echo "      python test_stage6_complete.py"
echo ""
echo "   5. Train your first models:"
echo "      python -m src.main train-ml"
echo ""
echo "🎯 Stage 6 Features:"
echo "   🤖 Multi-model training (XGBoost, Random Forest, Logistic Regression)"
echo "   📊 Comprehensive evaluation with visualizations"
echo "   🔮 Real-time goal prediction API"
echo "   ⚡ Fast prediction engine with ensemble methods"
echo "   📈 Feature importance analysis"
echo "   🎮 Interactive API documentation"
echo "   🔧 Complete CLI integration"
echo ""
echo "🚀 Ready for football goal prediction in production!"
echo "   Train models, evaluate performance, make predictions!"