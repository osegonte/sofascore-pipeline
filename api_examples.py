#!/usr/bin/env python3
"""
Stage 6 ML API Examples

Example usage of the prediction API endpoints.
"""

import requests
import json
import asyncio
from datetime import datetime

API_BASE = "http://localhost:8001"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("🔍 Testing health endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"   Models loaded: {data['models_loaded']}")
            print(f"   Targets available: {data['targets_available']}")
            print(f"   Uptime: {data['uptime_seconds']:.1f}s")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_models_endpoint():
    """Test the models listing endpoint."""
    print("\n📋 Testing models endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_models']} models")
            
            for target, models in data['models_by_target'].items():
                print(f"   {target}: {len(models)} models")
                for model in models[:2]:  # Show first 2
                    print(f"     - {model['name']} (F1: {model['f1_score']:.3f})")
        else:
            print(f"❌ Models listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Models listing error: {e}")

def test_prediction_endpoint():
    """Test the prediction endpoint."""
    print("\n🎯 Testing prediction endpoint...")
    
    # Test scenarios
    scenarios = [
        {
            "name": "Late game tie",
            "match_id": 12345,
            "minute": 85,
            "home_team_id": 1,
            "away_team_id": 2,
            "current_score_home": 1,
            "current_score_away": 1
        },
        {
            "name": "Losing team pressure",
            "match_id": 12346,
            "minute": 70,
            "home_team_id": 1,
            "away_team_id": 2,
            "current_score_home": 0,
            "current_score_away": 1
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   Testing: {scenario['name']}")
        
        try:
            response = requests.post(f"{API_BASE}/predict", json=scenario)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Prediction successful")
                print(f"      Processing time: {data['processing_time_ms']:.1f}ms")
                print(f"      Confidence: {data['confidence_score']:.3f}")
                
                print(f"      Ensemble predictions:")
                for target, prob in data['ensemble_prediction'].items():
                    timeframe = target.replace('goal_next_', '').replace('_any', '')
                    print(f"        Next {timeframe}: {prob:.1%}")
            else:
                print(f"   ❌ Prediction failed: {response.status_code}")
                print(f"      {response.text}")
        except Exception as e:
            print(f"   ❌ Prediction error: {e}")

def test_timeframe_endpoint():
    """Test the timeframe-specific prediction endpoint."""
    print("\n⏱️  Testing timeframe endpoint...")
    
    match_state = {
        "match_id": 12345,
        "minute": 75,
        "home_team_id": 1,
        "away_team_id": 2,
        "current_score_home": 2,
        "current_score_away": 0
    }
    
    timeframes = [1, 5, 15]
    
    for timeframe in timeframes:
        try:
            response = requests.post(f"{API_BASE}/predict/timeframe/{timeframe}", json=match_state)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {timeframe}min prediction: {data['probability']:.1%} (confidence: {data['confidence']:.2f})")
            else:
                print(f"   ❌ {timeframe}min prediction failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {timeframe}min prediction error: {e}")

def main():
    """Run all API tests."""
    print("🚀 Stage 6 ML API Testing")
    print("=" * 40)
    print("Make sure the API server is running:")
    print("  python -m src.main serve-ml")
    print("")
    
    test_health_endpoint()
    test_models_endpoint()
    test_prediction_endpoint()
    test_timeframe_endpoint()
    
    print("\n✅ API testing completed!")
    print("📚 Full API documentation: http://localhost:8001/docs")

if __name__ == "__main__":
    main()
