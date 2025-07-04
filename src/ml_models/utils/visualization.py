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
