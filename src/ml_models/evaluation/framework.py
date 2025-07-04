"""
ML Model Evaluation Framework

Comprehensive evaluation and comparison of trained ML models
with visualizations and detailed metrics analysis.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import joblib

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve,
    confusion_matrix, classification_report
)
from sklearn.calibration import calibration_curve

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

logger = logging.getLogger('ml_models.evaluation')

@dataclass
class EvaluationResult:
    """Results from model evaluation."""
    model_name: str
    target_column: str
    model_path: str
    
    # Basic metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    auc: float = 0.0
    
    # Advanced metrics
    log_loss: float = 0.0
    precision_at_k: Dict[str, float] = field(default_factory=dict)
    recall_at_k: Dict[str, float] = field(default_factory=dict)
    
    # Probability analysis
    calibration_error: float = 0.0
    prediction_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Confusion matrix
    confusion_matrix: List[List[int]] = field(default_factory=list)
    
    # Feature analysis
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    test_samples: int = 0
    positive_samples: int = 0
    negative_samples: int = 0
    evaluation_time: float = 0.0
    timestamp: str = ""

@dataclass
class ComparisonResult:
    """Results from model comparison."""
    target_column: str
    models_compared: List[str]
    best_model: str
    best_metric_value: float
    metric_used: str
    
    # Detailed comparison
    model_rankings: Dict[str, int] = field(default_factory=dict)
    metric_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Statistical significance
    significance_tests: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    timestamp: str = ""

class ModelEvaluator:
    """Comprehensive model evaluation framework."""
    
    def __init__(self, output_dir: str = "data/models/evaluation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "plots").mkdir(exist_ok=True)
        (self.output_dir / "comparisons").mkdir(exist_ok=True)
    
    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Load saved model and metadata."""
        try:
            model_data = joblib.load(model_path)
            logger.debug(f"Loaded model from {model_path}")
            return model_data
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            raise
    
    def prepare_test_data(self, data_path: str, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare test data for evaluation."""
        # Load data
        data = pd.read_csv(data_path)
        
        # Define feature exclusions
        exclude_cols = [
            'match_id', 'minute', 'home_team_id', 'away_team_id',
            'feature_generated_at', 'goal_next_1min_any', 
            'goal_next_5min_any', 'goal_next_15min_any'
        ]
        
        # Prepare features and target
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        X = data[feature_cols].fillna(0).values
        y = data[target_column].values
        
        return X, y
    
    def apply_preprocessing(self, model_data: Dict, X: np.ndarray) -> np.ndarray:
        """Apply the same preprocessing used during training."""
        X_processed = X.copy()
        
        # Apply feature selection if used during training
        if model_data.get('feature_selector'):
            feature_selector = model_data['feature_selector']
            if isinstance(feature_selector, dict):
                # Handle combined selectors
                X_processed = feature_selector['variance_selector'].transform(X_processed)
                X_processed = feature_selector['mi_selector'].transform(X_processed)
            else:
                X_processed = feature_selector.transform(X_processed)
        
        # Apply scaling if used during training
        if model_data.get('scaler'):
            X_processed = model_data['scaler'].transform(X_processed)
        
        return X_processed
    
    def calculate_advanced_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, Any]:
        """Calculate advanced evaluation metrics."""
        metrics = {}
        
        # Precision and recall at different thresholds
        precision_at_k = {}
        recall_at_k = {}
        
        for k in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            y_pred_at_k = (y_proba >= k).astype(int)
            if len(np.unique(y_pred_at_k)) > 1:
                precision_at_k[f"precision_at_{k}"] = precision_score(y_true, y_pred_at_k, zero_division=0)
                recall_at_k[f"recall_at_{k}"] = recall_score(y_true, y_pred_at_k, zero_division=0)
        
        metrics['precision_at_k'] = precision_at_k
        metrics['recall_at_k'] = recall_at_k
        
        # Calibration analysis
        try:
            fraction_of_positives, mean_predicted_value = calibration_curve(y_true, y_proba, n_bins=10)
            calibration_error = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
            metrics['calibration_error'] = calibration_error
        except Exception as e:
            logger.warning(f"Could not calculate calibration error: {e}")
            metrics['calibration_error'] = 0.0
        
        # Prediction distribution
        metrics['prediction_distribution'] = {
            'mean_proba': float(np.mean(y_proba)),
            'std_proba': float(np.std(y_proba)),
            'min_proba': float(np.min(y_proba)),
            'max_proba': float(np.max(y_proba)),
            'median_proba': float(np.median(y_proba))
        }
        
        return metrics
    
    def evaluate_single_model(self, model_path: str, data_path: str, target_column: str) -> EvaluationResult:
        """Evaluate a single model comprehensively."""
        start_time = datetime.now()
        logger.info(f"Evaluating model: {Path(model_path).name} for target '{target_column}'")
        
        # Load model and data
        model_data = self.load_model(model_path)
        X_test, y_test = self.prepare_test_data(data_path, target_column)
        
        # Apply preprocessing
        X_test_processed = self.apply_preprocessing(model_data, X_test)
        
        # Make predictions
        model = model_data['model']
        y_pred = model.predict(X_test_processed)
        
        # Get probabilities if available
        y_proba = None
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test_processed)[:, 1]
        elif hasattr(model, 'decision_function'):
            # Convert decision function to probabilities (approximate)
            decision_scores = model.decision_function(X_test_processed)
            y_proba = 1 / (1 + np.exp(-decision_scores))  # Sigmoid transformation
        else:
            y_proba = y_pred.astype(float)  # Fallback to binary predictions
        
        # Calculate basic metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # AUC score
        auc = 0.0
        try:
            auc = roc_auc_score(y_test, y_proba)
        except Exception as e:
            logger.warning(f"Could not calculate AUC: {e}")
        
        # Log loss
        log_loss_val = 0.0
        try:
            from sklearn.metrics import log_loss
            # Clip probabilities to avoid log(0)
            y_proba_clipped = np.clip(y_proba, 1e-15, 1 - 1e-15)
            log_loss_val = log_loss(y_test, y_proba_clipped)
        except Exception as e:
            logger.warning(f"Could not calculate log loss: {e}")
        
        # Advanced metrics
        advanced_metrics = self.calculate_advanced_metrics(y_test, y_pred, y_proba)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        # Feature importance
        feature_importance = {}
        metadata = model_data.get('metadata', {})
        if 'feature_importance' in metadata:
            feature_importance = metadata['feature_importance']
        
        # Calculate evaluation time
        evaluation_time = (datetime.now() - start_time).total_seconds()
        
        # Create result object
        result = EvaluationResult(
            model_name=metadata.get('model_name', 'unknown'),
            target_column=target_column,
            model_path=model_path,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            auc=auc,
            log_loss=log_loss_val,
            precision_at_k=advanced_metrics['precision_at_k'],
            recall_at_k=advanced_metrics['recall_at_k'],
            calibration_error=advanced_metrics['calibration_error'],
            prediction_distribution=advanced_metrics['prediction_distribution'],
            confusion_matrix=cm,
            feature_importance=feature_importance,
            test_samples=len(y_test),
            positive_samples=int(np.sum(y_test)),
            negative_samples=int(len(y_test) - np.sum(y_test)),
            evaluation_time=evaluation_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Evaluation completed - F1: {f1:.4f}, AUC: {auc:.4f}, Accuracy: {accuracy:.4f}")
        return result
    
    def evaluate_multiple_models(self, model_paths: List[str], data_path: str, target_column: str) -> List[EvaluationResult]:
        """Evaluate multiple models on the same dataset."""
        results = []
        
        logger.info(f"Evaluating {len(model_paths)} models for target '{target_column}'")
        
        for model_path in model_paths:
            try:
                result = self.evaluate_single_model(model_path, data_path, target_column)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate {model_path}: {e}")
                continue
        
        return results
    
    def compare_models(self, results: List[EvaluationResult], metric: str = 'f1') -> ComparisonResult:
        """Compare multiple models and rank them."""
        if not results:
            raise ValueError("No evaluation results provided")
        
        # Check if all results are for the same target
        target_column = results[0].target_column
        if not all(r.target_column == target_column for r in results):
            raise ValueError("All results must be for the same target column")
        
        # Extract metric values
        metric_values = {}
        for result in results:
            if hasattr(result, metric):
                metric_values[result.model_name] = getattr(result, metric)
            else:
                logger.warning(f"Metric '{metric}' not found in result for {result.model_name}")
                metric_values[result.model_name] = 0.0
        
        # Rank models
        sorted_models = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
        model_rankings = {model: rank + 1 for rank, (model, _) in enumerate(sorted_models)}
        
        # Best model
        best_model = sorted_models[0][0]
        best_metric_value = sorted_models[0][1]
        
        # Create detailed comparison
        metric_comparison = {}
        for result in results:
            metric_comparison[result.model_name] = {
                'accuracy': result.accuracy,
                'precision': result.precision,
                'recall': result.recall,
                'f1': result.f1,
                'auc': result.auc,
                'log_loss': result.log_loss
            }
        
        comparison_result = ComparisonResult(
            target_column=target_column,
            models_compared=[r.model_name for r in results],
            best_model=best_model,
            best_metric_value=best_metric_value,
            metric_used=metric,
            model_rankings=model_rankings,
            metric_comparison=metric_comparison,
            timestamp=datetime.now().isoformat()
        )
        
        return comparison_result
    
    def generate_evaluation_report(self, results: List[EvaluationResult]) -> str:
        """Generate comprehensive evaluation report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / "reports" / f"evaluation_report_{timestamp}.json"
        
        # Prepare report data
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_models': len(results),
            'targets_evaluated': list(set(r.target_column for r in results)),
            'summary': {
                'best_models_by_target': {},
                'average_metrics': {},
                'model_performance': {}
            },
            'detailed_results': []
        }
        
        # Group results by target
        results_by_target = {}
        for result in results:
            if result.target_column not in results_by_target:
                results_by_target[result.target_column] = []
            results_by_target[result.target_column].append(result)
        
        # Analyze each target
        for target, target_results in results_by_target.items():
            # Find best model for this target
            best_result = max(target_results, key=lambda r: r.f1)
            report['summary']['best_models_by_target'][target] = {
                'model_name': best_result.model_name,
                'f1_score': best_result.f1,
                'accuracy': best_result.accuracy,
                'auc': best_result.auc
            }
            
            # Calculate average metrics for this target
            if target_results:
                avg_metrics = {
                    'accuracy': np.mean([r.accuracy for r in target_results]),
                    'precision': np.mean([r.precision for r in target_results]),
                    'recall': np.mean([r.recall for r in target_results]),
                    'f1': np.mean([r.f1 for r in target_results]),
                    'auc': np.mean([r.auc for r in target_results])
                }
                report['summary']['average_metrics'][target] = avg_metrics
        
        # Add detailed results
        for result in results:
            result_dict = {
                'model_name': result.model_name,
                'target_column': result.target_column,
                'metrics': {
                    'accuracy': result.accuracy,
                    'precision': result.precision,
                    'recall': result.recall,
                    'f1': result.f1,
                    'auc': result.auc,
                    'log_loss': result.log_loss
                },
                'test_samples': result.test_samples,
                'positive_samples': result.positive_samples,
                'evaluation_time': result.evaluation_time,
                'top_features': list(result.feature_importance.keys())[:10] if result.feature_importance else [],
                'prediction_stats': result.prediction_distribution
            }
            report['detailed_results'].append(result_dict)
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Evaluation report saved: {report_path}")
        return str(report_path)
    
    def create_performance_plots(self, results: List[EvaluationResult], save_plots: bool = True) -> Dict[str, Any]:
        """Create performance visualization plots."""
        if not results:
            return {}
        
        plots_created = {}
        
        # Group results by target
        results_by_target = {}
        for result in results:
            if result.target_column not in results_by_target:
                results_by_target[result.target_column] = []
            results_by_target[result.target_column].append(result)
        
        # Create plots for each target
        for target, target_results in results_by_target.items():
            target_plots = self._create_target_plots(target, target_results, save_plots)
            plots_created[target] = target_plots
        
        return plots_created
    
    def _create_target_plots(self, target: str, results: List[EvaluationResult], save_plots: bool) -> Dict[str, str]:
        """Create plots for a specific target."""
        plots = {}
        
        # Model comparison bar plot
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Model Performance Comparison - {target}', fontsize=16)
        
        models = [r.model_name for r in results]
        metrics = ['accuracy', 'precision', 'recall', 'f1']
        
        for i, metric in enumerate(metrics):
            ax = axes[i // 2, i % 2]
            values = [getattr(r, metric) for r in results]
            
            bars = ax.bar(models, values, alpha=0.7)
            ax.set_title(f'{metric.capitalize()} Scores')
            ax.set_ylabel(metric.capitalize())
            ax.set_ylim(0, 1)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{value:.3f}', ha='center', va='bottom')
            
            # Rotate x-axis labels if needed
            if len(models) > 3:
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_plots:
            plot_path = self.output_dir / "plots" / f"model_comparison_{target}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plots['comparison'] = str(plot_path)
        
        plt.close()
        
        # Feature importance plot (for best model)
        best_result = max(results, key=lambda r: r.f1)
        if best_result.feature_importance:
            self._create_feature_importance_plot(target, best_result, save_plots, plots)
        
        # ROC curves comparison (if we have probability predictions)
        try:
            self._create_roc_comparison_plot(target, results, save_plots, plots)
        except Exception as e:
            logger.warning(f"Could not create ROC plot for {target}: {e}")
        
        return plots
    
    def _create_feature_importance_plot(self, target: str, result: EvaluationResult, save_plots: bool, plots: Dict):
        """Create feature importance plot."""
        # Get top features
        top_features = dict(list(result.feature_importance.items())[:15])
        
        if not top_features:
            return
        
        plt.figure(figsize=(10, 8))
        features = list(top_features.keys())
        importances = list(top_features.values())
        
        # Create horizontal bar plot
        y_pos = np.arange(len(features))
        plt.barh(y_pos, importances, alpha=0.7)
        plt.yticks(y_pos, features)
        plt.xlabel('Feature Importance')
        plt.title(f'Top Feature Importance - {result.model_name} ({target})')
        plt.gca().invert_yaxis()  # Top feature at the top
        
        plt.tight_layout()
        
        if save_plots:
            plot_path = self.output_dir / "plots" / f"feature_importance_{target}_{result.model_name}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plots['feature_importance'] = str(plot_path)
        
        plt.close()
    
    def _create_roc_comparison_plot(self, target: str, results: List[EvaluationResult], save_plots: bool, plots: Dict):
        """Create ROC curve comparison plot."""
        plt.figure(figsize=(10, 8))
        
        # We would need access to the actual predictions to create ROC curves
        # For now, create a placeholder showing AUC scores
        models = [r.model_name for r in results]
        auc_scores = [r.auc for r in results]
        
        # Create AUC comparison
        bars = plt.bar(models, auc_scores, alpha=0.7)
        plt.title(f'AUC Score Comparison - {target}')
        plt.ylabel('AUC Score')
        plt.ylim(0, 1)
        
        # Add value labels
        for bar, score in zip(bars, auc_scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.3f}', ha='center', va='bottom')
        
        if len(models) > 3:
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_plots:
            plot_path = self.output_dir / "plots" / f"auc_comparison_{target}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plots['auc_comparison'] = str(plot_path)
        
        plt.close()
    
    def create_interactive_dashboard(self, results: List[EvaluationResult]) -> str:
        """Create interactive dashboard using Plotly (if available)."""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available, skipping interactive dashboard")
            return ""
        
        # Create interactive plots
        dashboard_path = self.output_dir / "reports" / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Group results by target
        results_by_target = {}
        for result in results:
            if result.target_column not in results_by_target:
                results_by_target[result.target_column] = []
            results_by_target[result.target_column].append(result)
        
        # Create subplots
        n_targets = len(results_by_target)
        fig = make_subplots(
            rows=n_targets, cols=2,
            subplot_titles=[f'{target} - Metrics' for target in results_by_target.keys()] + 
                          [f'{target} - AUC' for target in results_by_target.keys()],
            specs=[[{"type": "bar"}, {"type": "bar"}] for _ in range(n_targets)]
        )
        
        # Add plots for each target
        for i, (target, target_results) in enumerate(results_by_target.items(), 1):
            models = [r.model_name for r in target_results]
            
            # Metrics comparison
            for metric in ['accuracy', 'precision', 'recall', 'f1']:
                values = [getattr(r, metric) for r in target_results]
                fig.add_trace(
                    go.Bar(x=models, y=values, name=f'{metric}_{target}', 
                          legendgroup=f'group{i}', showlegend=True),
                    row=i, col=1
                )
            
            # AUC scores
            auc_values = [r.auc for r in target_results]
            fig.add_trace(
                go.Bar(x=models, y=auc_values, name=f'AUC_{target}',
                      legendgroup=f'group{i}', showlegend=True),
                row=i, col=2
            )
        
        # Update layout
        fig.update_layout(
            title="ML Model Performance Dashboard",
            height=300 * n_targets,
            showlegend=True
        )
        
        # Save dashboard
        fig.write_html(dashboard_path)
        logger.info(f"Interactive dashboard saved: {dashboard_path}")
        
        return str(dashboard_path)
    
    def export_results_to_csv(self, results: List[EvaluationResult]) -> str:
        """Export evaluation results to CSV format."""
        if not results:
            return ""
        
        # Prepare data for CSV
        csv_data = []
        for result in results:
            row = {
                'model_name': result.model_name,
                'target_column': result.target_column,
                'accuracy': result.accuracy,
                'precision': result.precision,
                'recall': result.recall,
                'f1': result.f1,
                'auc': result.auc,
                'log_loss': result.log_loss,
                'test_samples': result.test_samples,
                'positive_samples': result.positive_samples,
                'evaluation_time': result.evaluation_time,
                'timestamp': result.timestamp
            }
            csv_data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        csv_path = self.output_dir / "reports" / f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Results exported to CSV: {csv_path}")
        return str(csv_path)