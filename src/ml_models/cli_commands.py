"""
CLI Commands for Stage 6 ML Model Development.
Comprehensive goal prediction pipeline.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from .training.pipeline import MLTrainingPipeline, TrainingConfig
    from .evaluation.framework import ModelEvaluator
    from .prediction.api import PredictionEngine, ModelManager, MatchState, run_api_server
    IMPLEMENTATIONS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ML implementations not fully available: {e}")
    IMPLEMENTATIONS_AVAILABLE = False

class MLCommandRunner:
    """Complete ML command runner for Stage 6."""
    
    def __init__(self):
        self.training_pipeline = None
        self.evaluator = None
        self.prediction_engine = None
        self.config_path = Path("config/ml_models")
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration file."""
        config_file = self.config_path / f"{config_name}.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return {}
    
    async def run_training(self, training_data: str, target: Optional[str] = None, 
                          models: Optional[List[str]] = None) -> bool:
        """Run comprehensive ML model training."""
        print(f"🎯 Starting Stage 6 ML Training Pipeline...")
        print(f"   Training Data: {training_data}")
        print(f"   Target: {target or 'all targets'}")
        print(f"   Models: {models or 'all models'}")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ Full ML implementations not available. Install requirements:")
            print("   pip install -r requirements_ml.txt")
            return False
        
        try:
            # Load training configuration
            training_config = self.load_config("training_config")
            config = TrainingConfig.from_dict(training_config)
            
            # Initialize training pipeline
            self.training_pipeline = MLTrainingPipeline(config)
            
            # Load and validate training data
            if not Path(training_data).exists():
                print(f"❌ Training data file not found: {training_data}")
                return False
            
            data = self.training_pipeline.load_training_data(training_data)
            print(f"✅ Loaded {len(data)} training examples with {len(data.columns)} features")
            
            # Display data summary
            print(f"\n📊 Training Data Summary:")
            for col in ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']:
                if col in data.columns:
                    positive_count = data[col].sum()
                    total_count = len(data)
                    print(f"   {col}: {positive_count}/{total_count} ({positive_count/total_count*100:.1f}% positive)")
            
            # Train models
            if target and target in data.columns:
                # Train models for specific target
                print(f"\n🔄 Training models for target: {target}")
                target_results = self.training_pipeline.train_all_models(target, models)
                
                print(f"\n📊 Training Results for {target}:")
                for model_name, result in target_results.items():
                    print(f"   {model_name}:")
                    print(f"     F1 Score: {result.test_f1:.3f}")
                    print(f"     Accuracy: {result.test_accuracy:.3f}")
                    print(f"     AUC: {result.auc_score:.3f}")
                    print(f"     Training Time: {result.training_time:.1f}s")
            else:
                # Train models for all targets
                print(f"\n🔄 Training models for all targets...")
                all_results = self.training_pipeline.train_all_targets(models)
                
                print(f"\n📊 Training Summary:")
                for target_col, target_results in all_results.items():
                    if target_results:
                        best_result = max(target_results.values(), key=lambda r: r.test_f1)
                        print(f"   {target_col}:")
                        print(f"     Best Model: {best_result.model_name}")
                        print(f"     Best F1: {best_result.test_f1:.3f}")
                        print(f"     Best Accuracy: {best_result.test_accuracy:.3f}")
                        print(f"     Models Trained: {len(target_results)}")
            
            print(f"\n✅ Training completed successfully!")
            print(f"📁 Models saved to: data/models/saved_models/")
            return True
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_evaluation(self, test_data: str, models_dir: Optional[str] = None, 
                           create_plots: bool = True) -> bool:
        """Run comprehensive model evaluation."""
        print(f"📊 Starting Stage 6 Model Evaluation...")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ ML implementations not available.")
            return False
        
        try:
            # Load evaluation configuration
            eval_config = self.load_config("evaluation_config")
            
            # Initialize evaluator
            self.evaluator = ModelEvaluator(output_dir="data/models/evaluation")
            
            # Load test data
            if not Path(test_data).exists():
                print(f"❌ Test data file not found: {test_data}")
                return False
            
            data = pd.read_csv(test_data)
            print(f"✅ Loaded {len(data)} test examples")
            
            # Find model files
            models_path = Path(models_dir) if models_dir else Path("data/models/saved_models")
            if not models_path.exists():
                print(f"❌ Models directory not found: {models_path}")
                return False
            
            model_files = list(models_path.glob("*.joblib"))
            if not model_files:
                print(f"❌ No model files found in {models_path}")
                print("   Train models first with: python -m src.main train-ml")
                return False
            
            print(f"✅ Found {len(model_files)} model files")
            
            # Evaluate models for each target
            all_results = []
            targets = ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']
            
            for target in targets:
                if target not in data.columns:
                    print(f"⚠️  Target {target} not found in test data")
                    continue
                
                print(f"\n🔍 Evaluating models for target: {target}")
                target_model_files = [f for f in model_files if target in f.name]
                
                if not target_model_files:
                    print(f"   No models found for {target}")
                    continue
                
                for model_file in target_model_files:
                    try:
                        result = self.evaluator.evaluate_single_model(
                            str(model_file), str(test_data), target
                        )
                        all_results.append(result)
                        print(f"   ✅ {result.model_name}: F1={result.f1:.3f}, Acc={result.accuracy:.3f}, AUC={result.auc:.3f}")
                    except Exception as e:
                        print(f"   ❌ {model_file.name}: {e}")
            
            if not all_results:
                print("❌ No models successfully evaluated")
                return False
            
            # Generate comprehensive evaluation report
            print(f"\n📋 Generating evaluation report...")
            report_path = self.evaluator.generate_evaluation_report(all_results)
            print(f"✅ Evaluation report: {report_path}")
            
            # Create visualizations
            if create_plots:
                print(f"📊 Creating performance visualizations...")
                plots = self.evaluator.create_performance_plots(all_results)
                print(f"✅ Plots saved to: data/models/evaluation/plots/")
            
            # Export results to CSV
            csv_path = self.evaluator.export_results_to_csv(all_results)
            print(f"✅ Results exported to: {csv_path}")
            
            # Model comparison summary
            print(f"\n📈 Model Performance Summary:")
            targets_evaluated = list(set(r.target_column for r in all_results))
            for target in targets_evaluated:
                target_results = [r for r in all_results if r.target_column == target]
                if target_results:
                    best = max(target_results, key=lambda r: r.f1)
                    print(f"   {target}:")
                    print(f"     Best Model: {best.model_name} (F1: {best.f1:.3f})")
                    print(f"     Models Evaluated: {len(target_results)}")
            
            return True
                
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_prediction(self, match_id: int, minute: int, home_score: int, away_score: int, 
                           home_team_id: int = 1, away_team_id: int = 2) -> bool:
        """Run real-time prediction."""
        print(f"⚽ Making Goal Prediction...")
        print(f"   Match: {match_id}")
        print(f"   Current State: {home_score}-{away_score} at {minute}'")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ ML implementations not available.")
            return False
        
        try:
            # Initialize model manager and prediction engine
            model_manager = ModelManager()
            loaded_models = model_manager.load_best_models()
            
            if not loaded_models:
                print("❌ No models loaded. Train models first with:")
                print("   python -m src.main train-ml")
                return False
            
            print(f"✅ Loaded {len(loaded_models)} models")
            
            # Show loaded models by target
            discovered = model_manager.discover_models()
            for target, models in discovered.items():
                model_count = len([m for m in models if any(key.endswith(f"_{target}") for key in loaded_models.keys())])
                if model_count > 0:
                    print(f"   {target}: {model_count} models")
            
            self.prediction_engine = PredictionEngine(model_manager)
            
            # Create match state
            match_state = MatchState(
                match_id=match_id,
                minute=minute,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                current_score_home=home_score,
                current_score_away=away_score
            )
            
            # Make prediction
            result = self.prediction_engine.predict_all_targets(match_state)
            
            # Display results
            print(f"\n🎯 Goal Prediction Results:")
            print(f"   Match {match_id} ({home_score}-{away_score} at {minute}')")
            print(f"   Processing Time: {result.processing_time_ms:.1f}ms")
            print(f"   Overall Confidence: {result.confidence_score:.3f}")
            
            print(f"\n📊 Ensemble Predictions:")
            for target, probability in result.ensemble_prediction.items():
                timeframe = target.replace('goal_next_', '').replace('_any', '')
                print(f"   Next {timeframe}: {probability:.1%} chance")
            
            print(f"\n🤖 Individual Model Predictions:")
            for target, target_predictions in result.predictions.items():
                if target_predictions:
                    timeframe = target.replace('goal_next_', '').replace('_any', '')
                    print(f"   {timeframe}:")
                    for model_key, pred in target_predictions.items():
                        if 'error' not in pred:
                            model_name = model_key.split('_')[0]
                            print(f"     {model_name}: {pred['probability']:.1%} (conf: {pred['confidence']:.2f})")
            
            return True
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_prediction_demo(self) -> bool:
        """Run prediction demo with multiple scenarios."""
        print(f"🎮 Running Goal Prediction Demo...")
        
        scenarios = [
            {
                "name": "Late Game Tie", 
                "match_id": 12345, "minute": 85, "home_score": 1, "away_score": 1,
                "description": "Tight match in final minutes"
            },
            {
                "name": "Losing Team Pressure",
                "match_id": 12346, "minute": 70, "home_score": 0, "away_score": 1, 
                "description": "Home team needs to equalize"
            },
            {
                "name": "Comfortable Lead",
                "match_id": 12347, "minute": 75, "home_score": 2, "away_score": 0,
                "description": "Home team protecting lead"
            }
        ]
        
        success_count = 0
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📊 Scenario {i}: {scenario['name']}")
            print(f"   {scenario['description']}")
            
            success = await self.run_prediction(
                scenario['match_id'], scenario['minute'], 
                scenario['home_score'], scenario['away_score']
            )
            
            if success:
                success_count += 1
        
        print(f"\n✅ Demo completed: {success_count}/{len(scenarios)} scenarios successful")
        return success_count == len(scenarios)
    
    async def run_api_server(self, host: str = "0.0.0.0", port: int = 8001) -> bool:
        """Start the prediction API server."""
        print(f"🚀 Starting ML Prediction API Server...")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ ML implementations not available.")
            return False
        
        try:
            # Load API configuration
            api_config = self.load_config("prediction_config")
            
            # Override with command line parameters
            if api_config.get("api"):
                api_config["api"]["host"] = host
                api_config["api"]["port"] = port
            
            print(f"✅ Configuration loaded")
            print(f"📚 API Documentation: http://{host}:{port}/docs")
            print(f"🔄 Health Check: http://{host}:{port}/health")
            
            # Start server
            await run_api_server(host=host, port=port)
            return True
            
        except Exception as e:
            print(f"❌ API server failed: {e}")
            import traceback
            traceback.print_exc()
            return False

# Command functions for main.py integration
async def run_ml_training(training_data: str, target: Optional[str] = None, 
                         models: Optional[List[str]] = None) -> bool:
    """Train ML models."""
    runner = MLCommandRunner()
    return await runner.run_training(training_data, target, models)

async def run_ml_evaluation(test_data: str, models_dir: Optional[str] = None, 
                           create_plots: bool = True) -> bool:
    """Evaluate ML models."""
    runner = MLCommandRunner()
    return await runner.run_evaluation(test_data, models_dir, create_plots)

async def run_ml_prediction(match_id: int, minute: int, home_score: int, away_score: int, 
                           home_team_id: int = 1, away_team_id: int = 2) -> bool:
    """Make goal prediction."""
    runner = MLCommandRunner()
    return await runner.run_prediction(match_id, minute, home_score, away_score, home_team_id, away_team_id)

async def run_ml_demo() -> bool:
    """Run prediction demo."""
    runner = MLCommandRunner()
    return await runner.run_prediction_demo()

async def run_ml_api_server(host: str = "0.0.0.0", port: int = 8001) -> bool:
    """Start API server."""
    runner = MLCommandRunner()
    return await runner.run_api_server(host, port)

# Standalone testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cli_commands.py [train|evaluate|predict|demo|serve]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "train":
        asyncio.run(run_ml_training("demo_training_dataset.csv"))
    elif command == "evaluate":
        asyncio.run(run_ml_evaluation("demo_training_dataset.csv"))
    elif command == "predict":
        asyncio.run(run_ml_prediction(12345, 75, 1, 0))
    elif command == "demo":
        asyncio.run(run_ml_demo())
    elif command == "serve":
        asyncio.run(run_ml_api_server())
    else:
        print(f"Unknown command: {command}")
