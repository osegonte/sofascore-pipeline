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
