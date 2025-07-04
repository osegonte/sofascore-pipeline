"""
Stage 6: ML Model Development for Goal Prediction

Complete machine learning pipeline for predicting football goals
in 1, 5, and 15 minute windows during matches.
"""

__version__ = "1.0.0"
__author__ = "SofaScore Pipeline Team"

from .training.pipeline import MLTrainingPipeline, TrainingConfig
from .evaluation.framework import ModelEvaluator
from .prediction.api import PredictionEngine, ModelManager, MatchState

__all__ = [
    'MLTrainingPipeline',
    'TrainingConfig', 
    'ModelEvaluator',
    'PredictionEngine',
    'ModelManager',
    'MatchState'
]
