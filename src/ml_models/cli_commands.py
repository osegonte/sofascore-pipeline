"""
Working CLI Commands for Stage 6 ML Model Development.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional
import pandas as pd

# Import our basic implementations
try:
    from .training.pipeline import MLTrainingPipeline, TrainingConfig
    from .evaluation.framework import ModelEvaluator
    from .prediction.api import PredictionEngine, ModelManager, MatchState
    IMPLEMENTATIONS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Some ML implementations not available: {e}")
    IMPLEMENTATIONS_AVAILABLE = False

class MLCommandRunner:
    """Working ML command runner."""
    
    def __init__(self):
        self.training_pipeline = None
        self.evaluator = None
        self.prediction_engine = None
    
    async def run_training(self, training_data: str, target: Optional[str] = None, models: Optional[List[str]] = None):
        """Run ML model training."""
        print(f"🎯 Starting ML Training...")
        print(f"   Data: {training_data}")
        print(f"   Target: {target or 'all targets'}")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ ML implementations not available. Copy full code from artifacts.")
            return False
        
        try:
            config = TrainingConfig()
            self.training_pipeline = MLTrainingPipeline(config)
            
            # Load training data
            data = self.training_pipeline.load_training_data(training_data)
            print(f"✅ Loaded {len(data)} training examples")
            
            # Train models
            if target and target in data.columns:
                results = self.training_pipeline.train_all_models(target)
                print(f"📊 Training Results for {target}:")
                for model_name, result in results.items():
                    print(f"   {model_name}: F1={result.test_f1:.3f}, Acc={result.test_accuracy:.3f}")
            else:
                all_results = self.training_pipeline.train_all_targets()
                print(f"📊 Training Summary:")
                for target_col, target_results in all_results.items():
                    if target_results:
                        best_result = max(target_results.values(), key=lambda r: r.test_f1)
                        print(f"   {target_col}: Best={best_result.model_name} (F1={best_result.test_f1:.3f})")
            
            print(f"✅ Training completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    
    async def run_evaluation(self, test_data: str, models_dir: Optional[str] = None, create_plots: bool = True):
        """Run model evaluation."""
        print(f"📊 Starting ML Evaluation...")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ ML implementations not available. Copy full code from artifacts.")
            return False
        
        try:
            self.evaluator = ModelEvaluator()
            
            # Load test data
            data = pd.read_csv(test_data)
            print(f"✅ Loaded {len(data)} test examples")
            
            # Prepare test features
            exclude_cols = [
                'match_id', 'minute', 'home_team_id', 'away_team_id',
                'feature_generated_at', 'goal_next_1min_any', 
                'goal_next_5min_any', 'goal_next_15min_any'
            ]
            feature_cols = [col for col in data.columns if col not in exclude_cols]
            X_test = data[feature_cols].values
            y_test = data['goal_next_5min_any'].values  # Using 5min as example
            
            # Find and evaluate models
            models_path = Path(models_dir) if models_dir else Path("data/models/saved_models")
            model_files = list(models_path.glob("*.joblib"))
            
            if not model_files:
                print(f"❌ No model files found in {models_path}")
                return False
            
            print(f"✅ Found {len(model_files)} model files")
            
            evaluation_results = []
            for model_file in model_files:
                try:
                    result = self.evaluator.evaluate_single_model(str(model_file), X_test, y_test)
                    evaluation_results.append(result)
                    print(f"   {result.model_name}: F1={result.f1:.3f}, Acc={result.accuracy:.3f}")
                except Exception as e:
                    print(f"   ❌ {model_file.name}: {e}")
            
            if evaluation_results:
                report_path = self.evaluator.generate_evaluation_report(evaluation_results)
                print(f"✅ Evaluation report: {report_path}")
                return True
            else:
                print(f"❌ No models successfully evaluated")
                return False
                
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            return False
    
    async def run_prediction(self, match_id: int, minute: int, home_score: int, away_score: int, home_team_id: int = 1, away_team_id: int = 2):
        """Run real-time prediction."""
        print(f"⚽ Making prediction for match {match_id}...")
        
        if not IMPLEMENTATIONS_AVAILABLE:
            print("❌ ML implementations not available. Copy full code from artifacts.")
            return False
        
        try:
            model_manager = ModelManager()
            loaded_models = model_manager.load_all_models()
            
            if not loaded_models:
                print("❌ No models loaded. Train models first.")
                return False
            
            print(f"✅ Loaded {len(loaded_models)} models")
            
            self.prediction_engine = PredictionEngine(model_manager)
            
            match_state = MatchState(
                match_id=match_id,
                minute=minute,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                current_score_home=home_score,
                current_score_away=away_score
            )
            
            result = self.prediction_engine.predict(match_state)
            
            print(f"🎯 Predictions for Match {match_id} ({home_score}-{away_score} at {minute}'):")
            for model_key, pred in result['predictions'].items():
                print(f"   {model_key}: {pred['probability']:.3f} (conf: {pred['confidence']:.3f})")
            
            return True
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            return False
    
    async def run_prediction_demo(self):
        """Run prediction demo."""
        print(f"🎮 Running ML Prediction Demo...")
        
        scenarios = [
            {"match_id": 12345, "minute": 65, "home_score": 1, "away_score": 0},
            {"match_id": 12346, "minute": 85, "home_score": 0, "away_score": 0},
            {"match_id": 12347, "minute": 70, "home_score": 2, "away_score": 2}
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📊 Scenario {i}: {scenario['home_score']}-{scenario['away_score']} at {scenario['minute']}'")
            await self.run_prediction(**scenario)
        
        return True

# Command functions for main.py integration
async def run_ml_training(training_data: str, target: Optional[str] = None):
    runner = MLCommandRunner()
    return await runner.run_training(training_data, target)

async def run_ml_evaluation(test_data: str, models_dir: Optional[str] = None):
    runner = MLCommandRunner()
    return await runner.run_evaluation(test_data, models_dir)

async def run_ml_prediction(match_id: int, minute: int, home_score: int, away_score: int, home_team_id: int = 1, away_team_id: int = 2):
    runner = MLCommandRunner()
    return await runner.run_prediction(match_id, minute, home_score, away_score, home_team_id, away_team_id)

async def run_ml_demo():
    runner = MLCommandRunner()
    return await runner.run_prediction_demo()

async def run_ml_api_server(host: str = "0.0.0.0", port: int = 8001):
    print(f"🚀 ML API Server would start on {host}:{port}")
    print(f"Full implementation available once complete code is copied")
