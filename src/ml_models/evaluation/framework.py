"""
Basic ML Model Evaluation Framework.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

@dataclass
class EvaluationResult:
    """Results from model evaluation."""
    model_name: str
    target_column: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc: float
    confusion_matrix: List[List[int]]

class ModelEvaluator:
    """Basic model evaluation framework."""
    
    def __init__(self, output_dir: str = "data/models/evaluation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Load saved model."""
        return joblib.load(model_path)
    
    def evaluate_single_model(self, model_path: str, X_test: np.ndarray, y_test: np.ndarray) -> EvaluationResult:
        """Evaluate a single model."""
        model_data = self.load_model(model_path)
        model = model_data['model']
        metadata = model_data.get('metadata', {})
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_pred_proba)
        except:
            auc = 0.0
        
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        return EvaluationResult(
            model_name=metadata.get('model_name', 'unknown'),
            target_column=metadata.get('target_column', 'unknown'),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            auc=auc,
            confusion_matrix=cm
        )
    
    def compare_models(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Compare multiple models."""
        if not results:
            return {}
        
        best_f1 = max(results, key=lambda r: r.f1)
        return {
            'best_model': {
                'name': best_f1.model_name,
                'f1_score': best_f1.f1,
                'accuracy': best_f1.accuracy
            },
            'total_models': len(results)
        }
    
    def generate_evaluation_report(self, results: List[EvaluationResult]) -> str:
        """Generate evaluation report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_models': len(results),
            'results': [
                {
                    'model_name': r.model_name,
                    'target_column': r.target_column,
                    'f1_score': r.f1,
                    'accuracy': r.accuracy,
                    'auc': r.auc
                }
                for r in results
            ],
            'comparison': self.compare_models(results)
        }
        
        report_path = self.output_dir / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_path)
