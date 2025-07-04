"""
ML Prediction API

Real-time prediction API for goal prediction in football matches.
Supports multiple models and provides confidence estimates.
"""

import json
import numpy as np
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import joblib

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger('ml_models.prediction')

@dataclass
class MatchState:
    """Current state of a football match for prediction."""
    match_id: int
    minute: int
    home_team_id: int
    away_team_id: int
    current_score_home: int
    current_score_away: int
    
    # Optional additional features
    is_late_game: Optional[bool] = None
    is_extra_time: Optional[bool] = None
    score_difference: Optional[int] = None
    total_goals: Optional[int] = None

@dataclass
class PredictionResult:
    """Result of a goal prediction."""
    match_id: int
    minute: int
    predictions: Dict[str, Dict[str, float]]
    ensemble_prediction: Dict[str, float]
    confidence_score: float
    processing_time_ms: float
    model_versions: Dict[str, str]
    timestamp: str

class ModelManager:
    """Manages loading and caching of ML models."""
    
    def __init__(self, models_dir: str = "data/models/saved_models"):
        self.models_dir = Path(models_dir)
        self.loaded_models = {}
        self.model_metadata = {}
        self.last_loaded = {}
    
    def discover_models(self) -> Dict[str, List[str]]:
        """Discover available models by target."""
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return {}
        
        models_by_target = {}
        model_files = list(self.models_dir.glob("*.joblib"))
        
        for model_file in model_files:
            try:
                # Load model metadata to get target
                model_data = joblib.load(model_file)
                metadata = model_data.get('metadata', {})
                target = metadata.get('target_column', 'unknown')
                model_name = metadata.get('model_name', 'unknown')
                
                if target not in models_by_target:
                    models_by_target[target] = []
                
                models_by_target[target].append({
                    'file': str(model_file),
                    'name': model_name,
                    'target': target,
                    'timestamp': metadata.get('timestamp', ''),
                    'f1_score': metadata.get('test_f1', 0),
                    'accuracy': metadata.get('test_accuracy', 0)
                })
                
            except Exception as e:
                logger.warning(f"Could not load model metadata from {model_file}: {e}")
                continue
        
        # Sort models by performance (F1 score)
        for target in models_by_target:
            models_by_target[target].sort(key=lambda x: x['f1_score'], reverse=True)
        
        logger.info(f"Discovered models for targets: {list(models_by_target.keys())}")
        return models_by_target
    
    def load_best_models(self, max_models_per_target: int = 3) -> Dict[str, Any]:
        """Load the best performing models for each target."""
        discovered = self.discover_models()
        
        for target, models in discovered.items():
            # Load top N models for this target
            models_to_load = models[:max_models_per_target]
            
            for model_info in models_to_load:
                model_key = f"{model_info['name']}_{target}"
                
                try:
                    model_data = joblib.load(model_info['file'])
                    self.loaded_models[model_key] = model_data
                    self.model_metadata[model_key] = model_info
                    self.last_loaded[model_key] = datetime.now()
                    
                    logger.info(f"Loaded model: {model_key} (F1: {model_info['f1_score']:.3f})")
                    
                except Exception as e:
                    logger.error(f"Failed to load model {model_info['file']}: {e}")
                    continue
        
        logger.info(f"Loaded {len(self.loaded_models)} models total")
        return self.loaded_models
    
    def get_models_for_target(self, target: str) -> Dict[str, Any]:
        """Get all loaded models for a specific target."""
        target_models = {}
        for key, model_data in self.loaded_models.items():
            if key.endswith(f"_{target}"):
                target_models[key] = model_data
        return target_models
    
    def reload_models_if_needed(self):
        """Reload models if they've been updated."""
        # Check if model files have been modified
        # This is a simplified version - in production you'd want more sophisticated caching
        current_files = set(self.models_dir.glob("*.joblib"))
        
        # For now, just log that we could check for updates
        logger.debug("Model update check completed")

class FeatureExtractor:
    """Extracts features from match state for prediction."""
    
    @staticmethod
    def extract_basic_features(match_state: MatchState) -> Dict[str, float]:
        """Extract basic features from match state."""
        features = {
            'current_score_home': float(match_state.current_score_home),
            'current_score_away': float(match_state.current_score_away),
            'score_difference': float(match_state.current_score_home - match_state.current_score_away),
            'total_goals': float(match_state.current_score_home + match_state.current_score_away),
            'is_late_game': float(match_state.minute >= 75),
            'is_extra_time': float(match_state.minute > 90)
        }
        
        return features
    
    @staticmethod
    def prepare_feature_vector(match_state: MatchState, required_features: Optional[List[str]] = None) -> np.ndarray:
        """Prepare feature vector for model prediction."""
        basic_features = FeatureExtractor.extract_basic_features(match_state)
        
        if required_features:
            # Use only the features that the model expects
            feature_vector = []
            for feature_name in required_features:
                if feature_name in basic_features:
                    feature_vector.append(basic_features[feature_name])
                else:
                    # Default value for missing features
                    feature_vector.append(0.0)
            return np.array(feature_vector).reshape(1, -1)
        else:
            # Use all basic features
            return np.array(list(basic_features.values())).reshape(1, -1)

class PredictionEngine:
    """Main prediction engine that coordinates models and features."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.feature_extractor = FeatureExtractor()
        
        # Prediction targets
        self.targets = ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']
        
        # Load models
        self.model_manager.load_best_models()
    
    def predict_single_model(self, model_key: str, model_data: Dict, features: np.ndarray) -> Dict[str, float]:
        """Make prediction with a single model."""
        try:
            # Apply preprocessing (feature selection and scaling)
            features_processed = self.apply_preprocessing(model_data, features)
            
            # Make prediction
            model = model_data['model']
            prediction = model.predict(features_processed)[0]
            
            # Get probability if available
            probability = 0.5  # Default
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(features_processed)[0][1]
            elif hasattr(model, 'decision_function'):
                # Convert decision function to probability
                decision_score = model.decision_function(features_processed)[0]
                probability = 1 / (1 + np.exp(-decision_score))
            else:
                probability = float(prediction)
            
            # Calculate confidence (distance from 0.5)
            confidence = abs(probability - 0.5) * 2
            
            return {
                'prediction': int(prediction),
                'probability': float(probability),
                'confidence': float(confidence)
            }
            
        except Exception as e:
            logger.error(f"Error in prediction for {model_key}: {e}")
            return {
                'prediction': 0,
                'probability': 0.5,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def apply_preprocessing(self, model_data: Dict, features: np.ndarray) -> np.ndarray:
        """Apply the same preprocessing used during training."""
        features_processed = features.copy()
        
        # Apply feature selection if used during training
        if model_data.get('feature_selector'):
            feature_selector = model_data['feature_selector']
            if isinstance(feature_selector, dict):
                # Handle combined selectors
                features_processed = feature_selector['variance_selector'].transform(features_processed)
                features_processed = feature_selector['mi_selector'].transform(features_processed)
            else:
                features_processed = feature_selector.transform(features_processed)
        
        # Apply scaling if used during training
        if model_data.get('scaler'):
            features_processed = model_data['scaler'].transform(features_processed)
        
        return features_processed
    
    def predict_all_targets(self, match_state: MatchState) -> PredictionResult:
        """Make predictions for all targets using all available models."""
        start_time = datetime.now()
        
        # Prepare features
        features = self.feature_extractor.prepare_feature_vector(match_state)
        
        # Store all predictions
        all_predictions = {}
        model_versions = {}
        
        # Make predictions for each target
        for target in self.targets:
            target_models = self.model_manager.get_models_for_target(target)
            target_predictions = {}
            
            for model_key, model_data in target_models.items():
                prediction_result = self.predict_single_model(model_key, model_data, features)
                target_predictions[model_key] = prediction_result
                
                # Store model version info
                metadata = model_data.get('metadata', {})
                model_versions[model_key] = metadata.get('timestamp', '')
            
            all_predictions[target] = target_predictions
        
        # Calculate ensemble predictions
        ensemble_predictions = self.calculate_ensemble_predictions(all_predictions)
        
        # Calculate overall confidence
        overall_confidence = self.calculate_overall_confidence(all_predictions)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create result
        result = PredictionResult(
            match_id=match_state.match_id,
            minute=match_state.minute,
            predictions=all_predictions,
            ensemble_prediction=ensemble_predictions,
            confidence_score=overall_confidence,
            processing_time_ms=processing_time,
            model_versions=model_versions,
            timestamp=datetime.now().isoformat()
        )
        
        return result
    
    def calculate_ensemble_predictions(self, all_predictions: Dict[str, Dict[str, Dict[str, float]]]) -> Dict[str, float]:
        """Calculate ensemble predictions by averaging model outputs."""
        ensemble = {}
        
        for target, target_predictions in all_predictions.items():
            if not target_predictions:
                ensemble[target] = 0.5
                continue
            
            # Average probabilities across models (weighted by confidence)
            total_weight = 0
            weighted_sum = 0
            
            for model_key, prediction in target_predictions.items():
                if 'error' not in prediction:
                    weight = prediction.get('confidence', 0.5)
                    probability = prediction.get('probability', 0.5)
                    
                    weighted_sum += probability * weight
                    total_weight += weight
            
            if total_weight > 0:
                ensemble[target] = weighted_sum / total_weight
            else:
                ensemble[target] = 0.5
        
        return ensemble
    
    def calculate_overall_confidence(self, all_predictions: Dict[str, Dict[str, Dict[str, float]]]) -> float:
        """Calculate overall confidence score across all predictions."""
        all_confidences = []
        
        for target, target_predictions in all_predictions.items():
            for model_key, prediction in target_predictions.items():
                if 'error' not in prediction:
                    all_confidences.append(prediction.get('confidence', 0.0))
        
        if all_confidences:
            return float(np.mean(all_confidences))
        else:
            return 0.0
    
    def predict_goals_in_timeframe(self, match_state: MatchState, timeframe_minutes: int) -> Dict[str, float]:
        """Predict probability of goals in specific timeframe."""
        # Map timeframe to target column
        target_mapping = {
            1: 'goal_next_1min_any',
            5: 'goal_next_5min_any',
            15: 'goal_next_15min_any'
        }
        
        if timeframe_minutes not in target_mapping:
            # Use the closest available timeframe
            closest = min(target_mapping.keys(), key=lambda x: abs(x - timeframe_minutes))
            target = target_mapping[closest]
            logger.warning(f"Timeframe {timeframe_minutes}min not available, using {closest}min")
        else:
            target = target_mapping[timeframe_minutes]
        
        # Get models for this target
        target_models = self.model_manager.get_models_for_target(target)
        
        if not target_models:
            logger.warning(f"No models available for target {target}")
            return {'probability': 0.5, 'confidence': 0.0}
        
        # Prepare features and make predictions
        features = self.feature_extractor.prepare_feature_vector(match_state)
        predictions = {}
        
        for model_key, model_data in target_models.items():
            prediction_result = self.predict_single_model(model_key, model_data, features)
            predictions[model_key] = prediction_result
        
        # Calculate ensemble result
        ensemble_prob = self.calculate_ensemble_predictions({target: predictions})[target]
        confidence = self.calculate_overall_confidence({target: predictions})
        
        return {
            'probability': ensemble_prob,
            'confidence': confidence,
            'timeframe_minutes': timeframe_minutes,
            'models_used': len(predictions)
        }

# FastAPI Application (if available)
if FASTAPI_AVAILABLE:
    
    # Pydantic models for API
    class MatchStateRequest(BaseModel):
        match_id: int = Field(..., description="Match ID")
        minute: int = Field(..., ge=0, le=150, description="Current minute")
        home_team_id: int = Field(..., description="Home team ID")
        away_team_id: int = Field(..., description="Away team ID")
        current_score_home: int = Field(..., ge=0, description="Home team score")
        current_score_away: int = Field(..., ge=0, description="Away team score")
    
    class PredictionResponse(BaseModel):
        match_id: int
        minute: int
        predictions: Dict[str, Dict[str, Dict[str, float]]]
        ensemble_prediction: Dict[str, float]
        confidence_score: float
        processing_time_ms: float
        timestamp: str
    
    class HealthResponse(BaseModel):
        status: str
        models_loaded: int
        targets_available: List[str]
        uptime_seconds: float
    
    class ModelInfo(BaseModel):
        name: str
        target: str
        f1_score: float
        accuracy: float
        timestamp: str
    
    class ModelsResponse(BaseModel):
        total_models: int
        models_by_target: Dict[str, List[ModelInfo]]
    
    # Create FastAPI app
    def create_app(model_manager: Optional[ModelManager] = None) -> FastAPI:
        """Create FastAPI application."""
        app = FastAPI(
            title="Football Goal Prediction API",
            description="Real-time goal prediction for football matches",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        if model_manager is None:
            model_manager = ModelManager()
        
        prediction_engine = PredictionEngine(model_manager)
        app_start_time = datetime.now()
        
        @app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            uptime = (datetime.now() - app_start_time).total_seconds()
            
            # Get available targets
            targets = []
            for target in prediction_engine.targets:
                if prediction_engine.model_manager.get_models_for_target(target):
                    targets.append(target)
            
            return HealthResponse(
                status="healthy",
                models_loaded=len(prediction_engine.model_manager.loaded_models),
                targets_available=targets,
                uptime_seconds=uptime
            )
        
        @app.get("/models", response_model=ModelsResponse)
        async def list_models():
            """List all available models."""
            discovered = prediction_engine.model_manager.discover_models()
            
            models_by_target = {}
            total_models = 0
            
            for target, models in discovered.items():
                model_info_list = []
                for model in models:
                    model_info = ModelInfo(
                        name=model['name'],
                        target=model['target'],
                        f1_score=model['f1_score'],
                        accuracy=model['accuracy'],
                        timestamp=model['timestamp']
                    )
                    model_info_list.append(model_info)
                    total_models += 1
                
                models_by_target[target] = model_info_list
            
            return ModelsResponse(
                total_models=total_models,
                models_by_target=models_by_target
            )
        
        @app.post("/predict", response_model=PredictionResponse)
        async def predict_goals(match_state: MatchStateRequest):
            """Predict goal probability for current match state."""
            try:
                # Convert request to MatchState
                state = MatchState(
                    match_id=match_state.match_id,
                    minute=match_state.minute,
                    home_team_id=match_state.home_team_id,
                    away_team_id=match_state.away_team_id,
                    current_score_home=match_state.current_score_home,
                    current_score_away=match_state.current_score_away
                )
                
                # Make prediction
                result = prediction_engine.predict_all_targets(state)
                
                return PredictionResponse(
                    match_id=result.match_id,
                    minute=result.minute,
                    predictions=result.predictions,
                    ensemble_prediction=result.ensemble_prediction,
                    confidence_score=result.confidence_score,
                    processing_time_ms=result.processing_time_ms,
                    timestamp=result.timestamp
                )
                
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
        
        @app.post("/predict/timeframe/{timeframe}")
        async def predict_timeframe(timeframe: int, match_state: MatchStateRequest):
            """Predict goal probability for specific timeframe."""
            try:
                # Convert request to MatchState
                state = MatchState(
                    match_id=match_state.match_id,
                    minute=match_state.minute,
                    home_team_id=match_state.home_team_id,
                    away_team_id=match_state.away_team_id,
                    current_score_home=match_state.current_score_home,
                    current_score_away=match_state.current_score_away
                )
                
                # Make prediction for specific timeframe
                result = prediction_engine.predict_goals_in_timeframe(state, timeframe)
                
                return {
                    "match_id": match_state.match_id,
                    "minute": match_state.minute,
                    "timeframe_minutes": timeframe,
                    "probability": result['probability'],
                    "confidence": result['confidence'],
                    "models_used": result['models_used']
                }
                
            except Exception as e:
                logger.error(f"Timeframe prediction error: {e}")
                raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
        
        @app.post("/models/reload")
        async def reload_models(background_tasks: BackgroundTasks):
            """Reload models in the background."""
            def reload():
                try:
                    prediction_engine.model_manager.load_best_models()
                    logger.info("Models reloaded successfully")
                except Exception as e:
                    logger.error(f"Model reload failed: {e}")
            
            background_tasks.add_task(reload)
            return {"status": "Model reload initiated"}
        
        return app

# Standalone prediction functions for CLI usage
async def run_api_server(host: str = "0.0.0.0", port: int = 8001, reload: bool = False):
    """Run the FastAPI server."""
    if not FASTAPI_AVAILABLE:
        logger.error("FastAPI not available. Install with: pip install fastapi uvicorn")
        return
    
    # Create app
    app = create_app()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    logger.info(f"Starting prediction API server on {host}:{port}")
    logger.info(f"API documentation available at http://{host}:{port}/docs")
    
    await server.serve()

def predict_match_state(match_state: MatchState) -> PredictionResult:
    """Standalone function to predict match state without API."""
    model_manager = ModelManager()
    prediction_engine = PredictionEngine(model_manager)
    
    return prediction_engine.predict_all_targets(match_state)

def predict_demo_scenarios() -> List[PredictionResult]:
    """Run prediction on demo scenarios."""
    model_manager = ModelManager()
    prediction_engine = PredictionEngine(model_manager)
    
    # Demo scenarios
    scenarios = [
        MatchState(match_id=12345, minute=65, home_team_id=1, away_team_id=2, 
                  current_score_home=1, current_score_away=0),
        MatchState(match_id=12346, minute=85, home_team_id=1, away_team_id=2,
                  current_score_home=0, current_score_away=0),
        MatchState(match_id=12347, minute=70, home_team_id=1, away_team_id=2,
                  current_score_home=2, current_score_away=2)
    ]
    
    results = []
    for scenario in scenarios:
        try:
            result = prediction_engine.predict_all_targets(scenario)
            results.append(result)
            
            print(f"\n🎯 Prediction for Match {scenario.match_id}:")
            print(f"   Minute: {scenario.minute}, Score: {scenario.current_score_home}-{scenario.current_score_away}")
            print(f"   Ensemble Predictions:")
            for target, prob in result.ensemble_prediction.items():
                print(f"     {target}: {prob:.3f}")
            print(f"   Confidence: {result.confidence_score:.3f}")
            
        except Exception as e:
            logger.error(f"Prediction failed for scenario {scenario.match_id}: {e}")
    
    return results