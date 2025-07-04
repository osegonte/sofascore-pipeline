"""
ML Training Pipeline for Goal Prediction

Comprehensive training pipeline supporting multiple ML models
for football goal prediction with hyperparameter tuning.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import logging

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, classification_report, confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif, VarianceThreshold
import joblib

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

logger = logging.getLogger('ml_models.training')

@dataclass
class TrainingConfig:
    """Configuration for ML training pipeline."""
    test_size: float = 0.2
    validation_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    model_save_path: str = "data/models/saved_models"
    experiment_path: str = "data/models/experiments"
    
    # Feature selection
    enable_feature_selection: bool = True
    max_features: int = 15
    variance_threshold: float = 0.01
    
    # Scaling
    enable_scaling: bool = True
    scaling_method: str = "standard"
    
    # Hyperparameter tuning
    enable_hyperparameter_tuning: bool = True
    tuning_method: str = "grid_search"  # "grid_search" or "optuna"
    max_trials: int = 50

@dataclass
class TrainingResult:
    """Results from model training."""
    model_name: str
    target_column: str
    model: Any = None
    scaler: Any = None
    feature_selector: Any = None
    
    # Metrics
    train_accuracy: float = 0.0
    test_accuracy: float = 0.0
    train_f1: float = 0.0
    test_f1: float = 0.0
    cv_scores: List[float] = field(default_factory=list)
    auc_score: float = 0.0
    
    # Training info
    training_time: float = 0.0
    best_params: Dict[str, Any] = field(default_factory=dict)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    selected_features: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

class MLTrainingPipeline:
    """Comprehensive ML training pipeline with multiple models."""
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        
        # Create directories
        Path(self.config.model_save_path).mkdir(parents=True, exist_ok=True)
        Path(self.config.experiment_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize data containers
        self.data = None
        self.feature_names = []
        
        # Target columns for goal prediction
        self.target_columns = [
            'goal_next_1min_any',
            'goal_next_5min_any', 
            'goal_next_15min_any'
        ]
        
        # Model definitions
        self.model_definitions = {
            'logistic_regression': {
                'class': LogisticRegression,
                'base_params': {
                    'random_state': self.config.random_state,
                    'max_iter': 1000
                },
                'param_grid': {
                    'C': [0.1, 1.0, 10.0],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear', 'lbfgs']
                }
            },
            'random_forest': {
                'class': RandomForestClassifier,
                'base_params': {
                    'random_state': self.config.random_state,
                    'n_jobs': -1
                },
                'param_grid': {
                    'n_estimators': [100, 200],
                    'max_depth': [5, 10, None],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2]
                }
            }
        }
        
        # Add XGBoost if available
        if XGBOOST_AVAILABLE:
            self.model_definitions['xgboost'] = {
                'class': xgb.XGBClassifier,
                'base_params': {
                    'random_state': self.config.random_state,
                    'eval_metric': 'logloss',
                    'use_label_encoder': False
                },
                'param_grid': {
                    'n_estimators': [100, 200],
                    'max_depth': [3, 6],
                    'learning_rate': [0.01, 0.1],
                    'subsample': [0.8, 1.0]
                }
            }
    
    def load_training_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate training data."""
        logger.info(f"Loading training data from {file_path}")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Training data file not found: {file_path}")
        
        self.data = pd.read_csv(file_path)
        logger.info(f"Loaded {len(self.data)} training examples with {len(self.data.columns)} features")
        
        # Validate required columns
        missing_targets = [col for col in self.target_columns if col not in self.data.columns]
        if missing_targets:
            logger.warning(f"Missing target columns: {missing_targets}")
        
        # Handle missing values
        self.data = self.data.fillna(0)
        
        return self.data
    
    def prepare_features(self, target_column: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare features and target for training."""
        # Define columns to exclude from features
        exclude_cols = [
            'match_id', 'minute', 'home_team_id', 'away_team_id',
            'feature_generated_at'
        ] + self.target_columns
        
        # Get feature columns
        feature_cols = [col for col in self.data.columns if col not in exclude_cols]
        
        # Prepare feature matrix and target vector
        X = self.data[feature_cols].values
        y = self.data[target_column].values
        
        # Handle any remaining NaN values
        X = np.nan_to_num(X, nan=0.0)
        
        logger.info(f"Prepared {X.shape[0]} samples with {X.shape[1]} features for target '{target_column}'")
        logger.info(f"Target distribution: {np.bincount(y)} (0s, 1s)")
        
        return X, y, feature_cols
    
    def apply_feature_selection(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Tuple[np.ndarray, Any, List[str]]:
        """Apply feature selection to reduce dimensionality."""
        if not self.config.enable_feature_selection:
            return X, None, feature_names
        
        logger.info(f"Applying feature selection (max_features={self.config.max_features})")
        
        # Remove low variance features
        variance_selector = VarianceThreshold(threshold=self.config.variance_threshold)
        X_variance = variance_selector.fit_transform(X)
        
        # Get remaining feature names after variance filtering
        variance_mask = variance_selector.get_support()
        remaining_features = [feature_names[i] for i in range(len(feature_names)) if variance_mask[i]]
        
        # Apply mutual information feature selection
        k_best = min(self.config.max_features, len(remaining_features))
        mi_selector = SelectKBest(score_func=mutual_info_classif, k=k_best)
        X_selected = mi_selector.fit_transform(X_variance, y)
        
        # Get final selected feature names
        mi_mask = mi_selector.get_support()
        selected_features = [remaining_features[i] for i in range(len(remaining_features)) if mi_mask[i]]
        
        logger.info(f"Selected {len(selected_features)} features: {selected_features[:5]}...")
        
        # Combine selectors
        feature_selector = {
            'variance_selector': variance_selector,
            'mi_selector': mi_selector,
            'selected_features': selected_features
        }
        
        return X_selected, feature_selector, selected_features
    
    def apply_scaling(self, X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Any]:
        """Apply feature scaling."""
        if not self.config.enable_scaling:
            return X_train, X_test, None
        
        logger.info(f"Applying {self.config.scaling_method} scaling")
        
        if self.config.scaling_method == "standard":
            scaler = StandardScaler()
        else:
            raise ValueError(f"Unknown scaling method: {self.config.scaling_method}")
        
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, scaler
    
    def optimize_hyperparameters(self, model_name: str, X_train: np.ndarray, y_train: np.ndarray) -> Tuple[Any, Dict[str, Any]]:
        """Optimize model hyperparameters."""
        if not self.config.enable_hyperparameter_tuning:
            # Return model with default parameters
            model_def = self.model_definitions[model_name]
            model = model_def['class'](**model_def['base_params'])
            return model, model_def['base_params']
        
        logger.info(f"Optimizing hyperparameters for {model_name}")
        
        model_def = self.model_definitions[model_name]
        
        if self.config.tuning_method == "grid_search":
            return self._grid_search_optimization(model_name, X_train, y_train)
        elif self.config.tuning_method == "optuna" and OPTUNA_AVAILABLE:
            return self._optuna_optimization(model_name, X_train, y_train)
        else:
            logger.warning(f"Hyperparameter tuning method '{self.config.tuning_method}' not available, using default params")
            model = model_def['class'](**model_def['base_params'])
            return model, model_def['base_params']
    
    def _grid_search_optimization(self, model_name: str, X_train: np.ndarray, y_train: np.ndarray) -> Tuple[Any, Dict[str, Any]]:
        """Grid search hyperparameter optimization."""
        model_def = self.model_definitions[model_name]
        
        # Create base model
        base_model = model_def['class'](**model_def['base_params'])
        
        # Perform grid search
        grid_search = GridSearchCV(
            base_model,
            model_def['param_grid'],
            cv=self.config.cv_folds,
            scoring='f1',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best params for {model_name}: {grid_search.best_params_}")
        logger.info(f"Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_, grid_search.best_params_
    
    def _optuna_optimization(self, model_name: str, X_train: np.ndarray, y_train: np.ndarray) -> Tuple[Any, Dict[str, Any]]:
        """Optuna hyperparameter optimization."""
        model_def = self.model_definitions[model_name]
        
        def objective(trial):
            # Suggest hyperparameters based on model type
            params = model_def['base_params'].copy()
            
            if model_name == 'logistic_regression':
                params['C'] = trial.suggest_float('C', 0.01, 10.0, log=True)
                params['penalty'] = trial.suggest_categorical('penalty', ['l1', 'l2'])
                if params['penalty'] == 'l1':
                    params['solver'] = 'liblinear'
                else:
                    params['solver'] = trial.suggest_categorical('solver', ['lbfgs', 'liblinear'])
            
            elif model_name == 'random_forest':
                params['n_estimators'] = trial.suggest_int('n_estimators', 50, 300)
                params['max_depth'] = trial.suggest_int('max_depth', 3, 20)
                params['min_samples_split'] = trial.suggest_int('min_samples_split', 2, 20)
                params['min_samples_leaf'] = trial.suggest_int('min_samples_leaf', 1, 10)
            
            elif model_name == 'xgboost':
                params['n_estimators'] = trial.suggest_int('n_estimators', 50, 300)
                params['max_depth'] = trial.suggest_int('max_depth', 3, 10)
                params['learning_rate'] = trial.suggest_float('learning_rate', 0.01, 0.3)
                params['subsample'] = trial.suggest_float('subsample', 0.6, 1.0)
                params['colsample_bytree'] = trial.suggest_float('colsample_bytree', 0.6, 1.0)
            
            # Create and evaluate model
            model = model_def['class'](**params)
            scores = cross_val_score(model, X_train, y_train, cv=self.config.cv_folds, scoring='f1')
            return scores.mean()
        
        # Run optimization
        study = optuna.create_study(direction='maximize', study_name=f"{model_name}_optimization")
        study.optimize(objective, n_trials=self.config.max_trials, show_progress_bar=False)
        
        # Get best parameters and create final model
        best_params = {**model_def['base_params'], **study.best_params}
        best_model = model_def['class'](**best_params)
        
        logger.info(f"Optuna best params for {model_name}: {study.best_params}")
        logger.info(f"Best CV score: {study.best_value:.4f}")
        
        return best_model, best_params
    
    def calculate_feature_importance(self, model: Any, feature_names: List[str]) -> Dict[str, float]:
        """Calculate and return feature importance."""
        importance_dict = {}
        
        try:
            if hasattr(model, 'feature_importances_'):
                # Tree-based models (RandomForest, XGBoost)
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                # Linear models (LogisticRegression)
                importances = np.abs(model.coef_[0])
            else:
                logger.warning(f"Cannot extract feature importance from {type(model)}")
                return importance_dict
            
            # Create importance dictionary
            for name, importance in zip(feature_names, importances):
                importance_dict[name] = float(importance)
            
            # Sort by importance
            importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
        
        return importance_dict
    
    def train_single_model(self, model_name: str, target_column: str) -> TrainingResult:
        """Train a single model for a specific target."""
        logger.info(f"Training {model_name} for target '{target_column}'")
        start_time = datetime.now()
        
        # Prepare data
        X, y, feature_names = self.prepare_features(target_column)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=y if len(np.unique(y)) > 1 else None
        )
        
        # Apply feature selection
        X_train_selected, feature_selector, selected_features = self.apply_feature_selection(
            X_train, y_train, feature_names
        )
        
        # Apply feature selection to test set
        if feature_selector:
            X_test_variance = feature_selector['variance_selector'].transform(X_test)
            X_test_selected = feature_selector['mi_selector'].transform(X_test_variance)
        else:
            X_test_selected = X_test
        
        # Apply scaling
        X_train_scaled, X_test_scaled, scaler = self.apply_scaling(X_train_selected, X_test_selected)
        
        # Optimize hyperparameters and train model
        model, best_params = self.optimize_hyperparameters(model_name, X_train_scaled, y_train)
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        train_f1 = f1_score(y_train, y_train_pred, zero_division=0)
        test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
        
        # AUC score
        auc_score = 0.0
        try:
            if hasattr(model, 'predict_proba'):
                y_test_proba = model.predict_proba(X_test_scaled)[:, 1]
                auc_score = roc_auc_score(y_test, y_test_proba)
        except Exception as e:
            logger.warning(f"Could not calculate AUC score: {e}")
        
        # Cross-validation scores
        cv_scores = []
        try:
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=self.config.cv_folds, scoring='f1')
            cv_scores = cv_scores.tolist()
        except Exception as e:
            logger.warning(f"Could not calculate CV scores: {e}")
        
        # Feature importance
        final_feature_names = selected_features if selected_features else feature_names
        feature_importance = self.calculate_feature_importance(model, final_feature_names)
        
        # Calculate training time
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Create result object
        result = TrainingResult(
            model_name=model_name,
            target_column=target_column,
            model=model,
            scaler=scaler,
            feature_selector=feature_selector,
            train_accuracy=train_accuracy,
            test_accuracy=test_accuracy,
            train_f1=train_f1,
            test_f1=test_f1,
            cv_scores=cv_scores,
            auc_score=auc_score,
            training_time=training_time,
            best_params=best_params,
            feature_importance=feature_importance,
            selected_features=final_feature_names,
            timestamp=datetime.now().isoformat(),
            config=self.config.__dict__
        )
        
        # Save model
        self.save_model(result)
        
        logger.info(f"Training completed - Test F1: {test_f1:.4f}, Test Accuracy: {test_accuracy:.4f}")
        return result
    
    def train_all_models(self, target_column: str) -> Dict[str, TrainingResult]:
        """Train all available models for a specific target."""
        results = {}
        
        logger.info(f"Training all models for target '{target_column}'")
        
        for model_name in self.model_definitions.keys():
            try:
                result = self.train_single_model(model_name, target_column)
                results[model_name] = result
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
                continue
        
        return results
    
    def train_all_targets(self) -> Dict[str, Dict[str, TrainingResult]]:
        """Train all models for all available targets."""
        all_results = {}
        
        available_targets = [col for col in self.target_columns if col in self.data.columns]
        
        for target in available_targets:
            logger.info(f"Training models for target '{target}'")
            target_results = self.train_all_models(target)
            all_results[target] = target_results
        
        # Save experiment summary
        self.save_experiment_summary(all_results)
        
        return all_results
    
    def save_model(self, result: TrainingResult):
        """Save trained model to disk."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{result.model_name}_{result.target_column}_{timestamp}.joblib"
        model_path = Path(self.config.model_save_path) / filename
        
        # Prepare model data
        model_data = {
            'model': result.model,
            'scaler': result.scaler,
            'feature_selector': result.feature_selector,
            'metadata': {
                'model_name': result.model_name,
                'target_column': result.target_column,
                'test_accuracy': result.test_accuracy,
                'test_f1': result.test_f1,
                'auc_score': result.auc_score,
                'best_params': result.best_params,
                'feature_importance': result.feature_importance,
                'selected_features': result.selected_features,
                'training_time': result.training_time,
                'timestamp': result.timestamp,
                'config': result.config
            }
        }
        
        # Save model
        joblib.dump(model_data, model_path)
        logger.info(f"Model saved: {model_path}")
    
    def save_experiment_summary(self, all_results: Dict[str, Dict[str, TrainingResult]]):
        """Save experiment summary to JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_path = Path(self.config.experiment_path) / f"experiment_{timestamp}.json"
        
        # Prepare summary data
        summary = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config.__dict__,
            'data_info': {
                'total_samples': len(self.data),
                'total_features': len(self.data.columns),
                'targets_trained': list(all_results.keys())
            },
            'results': {}
        }
        
        # Add results for each target
        for target, target_results in all_results.items():
            summary['results'][target] = {}
            for model_name, result in target_results.items():
                summary['results'][target][model_name] = {
                    'test_accuracy': result.test_accuracy,
                    'test_f1': result.test_f1,
                    'auc_score': result.auc_score,
                    'cv_mean': np.mean(result.cv_scores) if result.cv_scores else 0,
                    'cv_std': np.std(result.cv_scores) if result.cv_scores else 0,
                    'training_time': result.training_time,
                    'best_params': result.best_params,
                    'top_features': list(result.feature_importance.keys())[:10] if result.feature_importance else []
                }
        
        # Save summary
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Experiment summary saved: {summary_path}")
    
    def get_training_report(self, all_results: Dict[str, Dict[str, TrainingResult]]) -> Dict[str, Any]:
        """Generate comprehensive training report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_models_trained': sum(len(target_results) for target_results in all_results.values()),
            'targets': {},
            'best_models': {},
            'model_comparison': {}
        }
        
        # Analyze results for each target
        for target, target_results in all_results.items():
            if not target_results:
                continue
            
            # Find best model for this target
            best_model = max(target_results.values(), key=lambda r: r.test_f1)
            
            report['targets'][target] = {
                'models_trained': len(target_results),
                'best_model': best_model.model_name,
                'best_f1_score': best_model.test_f1,
                'best_accuracy': best_model.test_accuracy,
                'models_results': {
                    name: {
                        'f1_score': result.test_f1,
                        'accuracy': result.test_accuracy,
                        'auc_score': result.auc_score
                    }
                    for name, result in target_results.items()
                }
            }
            
            report['best_models'][target] = {
                'model_name': best_model.model_name,
                'f1_score': best_model.test_f1,
                'accuracy': best_model.test_accuracy,
                'auc_score': best_model.auc_score,
                'training_time': best_model.training_time
            }
        
        return report