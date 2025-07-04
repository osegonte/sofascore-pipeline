"""
Basic ML Training Pipeline for Python 3.13 compatibility.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import joblib

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

logger = logging.getLogger('ml_models.training')

@dataclass
class TrainingConfig:
    """Configuration for ML training."""
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    model_save_path: str = "data/models/saved_models"

@dataclass
class TrainingResult:
    """Results from model training."""
    model_name: str
    model: Any
    target_column: str
    test_accuracy: float = 0.0
    test_f1: float = 0.0
    training_time: float = 0.0
    timestamp: str = ""

class MLTrainingPipeline:
    """Basic ML training pipeline."""
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        Path(self.config.model_save_path).mkdir(parents=True, exist_ok=True)
        self.data = None
        
        self.target_columns = [
            'goal_next_1min_any',
            'goal_next_5min_any', 
            'goal_next_15min_any'
        ]
    
    def load_training_data(self, file_path: str) -> pd.DataFrame:
        """Load training data from CSV."""
        logger.info(f"Loading training data from {file_path}")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Training data file not found: {file_path}")
        
        self.data = pd.read_csv(file_path)
        logger.info(f"Loaded {len(self.data)} training examples")
        return self.data
    
    def prepare_features(self, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target."""
        exclude_cols = [
            'match_id', 'minute', 'home_team_id', 'away_team_id',
            'feature_generated_at'
        ] + self.target_columns
        
        feature_cols = [col for col in self.data.columns if col not in exclude_cols]
        X = self.data[feature_cols].values
        y = self.data[target_column].values
        
        X = np.nan_to_num(X, nan=0.0)
        return X, y
    
    def train_model(self, model_name: str, target_column: str) -> TrainingResult:
        """Train a single model."""
        start_time = datetime.now()
        
        X, y = self.prepare_features(target_column)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config.test_size, random_state=self.config.random_state
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Select and train model
        if model_name == 'random_forest':
            model = RandomForestClassifier(n_estimators=100, random_state=self.config.random_state)
        elif model_name == 'logistic_regression':
            model = LogisticRegression(random_state=self.config.random_state)
        elif model_name == 'xgboost' and XGBOOST_AVAILABLE:
            model = xgb.XGBClassifier(n_estimators=100, random_state=self.config.random_state)
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Train
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        test_accuracy = accuracy_score(y_test, y_pred)
        test_f1 = f1_score(y_test, y_pred, zero_division=0)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Save model
        model_data = {
            'model': model,
            'scaler': scaler,
            'metadata': {
                'model_name': model_name,
                'target_column': target_column,
                'test_accuracy': test_accuracy,
                'test_f1': test_f1,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        model_filename = f"{model_name}_{target_column}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        model_path = Path(self.config.model_save_path) / model_filename
        joblib.dump(model_data, model_path)
        
        result = TrainingResult(
            model_name=model_name,
            model=model,
            target_column=target_column,
            test_accuracy=test_accuracy,
            test_f1=test_f1,
            training_time=training_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Trained {model_name}: F1={test_f1:.3f}, Acc={test_accuracy:.3f}")
        return result
    
    def train_all_models(self, target_column: str) -> Dict[str, TrainingResult]:
        """Train all available models."""
        models = ['random_forest', 'logistic_regression']
        if XGBOOST_AVAILABLE:
            models.append('xgboost')
        
        results = {}
        for model_name in models:
            try:
                result = self.train_model(model_name, target_column)
                results[model_name] = result
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
        
        return results
    
    def train_all_targets(self) -> Dict[str, Dict[str, TrainingResult]]:
        """Train models for all targets."""
        all_results = {}
        
        for target in self.target_columns:
            if target in self.data.columns:
                logger.info(f"Training models for {target}")
                results = self.train_all_models(target)
                all_results[target] = results
        
        return all_results
    
    def generate_training_report(self) -> Dict[str, Any]:
        """Generate training report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'message': 'Training completed successfully'
        }
