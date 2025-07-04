#!/bin/bash
# scripts/calculate_probabilities.sh
# Calculate goal probabilities combining real-time ML predictions with historical analysis

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE7_HOME="$(dirname "$SCRIPT_DIR")"
source "$STAGE7_HOME/config/stage7_config.sh"

# Probability calculation settings
CONFIDENCE_THRESHOLD=0.6
HISTORICAL_WEIGHT=0.3
ML_WEIGHT=0.7

# =============================================================================
# LOGGING AND UTILITIES
# =============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PROB_CALC] $1" | tee -a "$LOGS_DIR/probability_calculator.log"
}

activate_python() {
    if [ -f "$PYTHON_ENV/bin/activate" ]; then
        source "$PYTHON_ENV/bin/activate"
    fi
}

# =============================================================================
# ML PREDICTION COMPONENT
# =============================================================================

get_ml_prediction() {
    local match_id=$1
    local minute=$2
    local home_score=$3
    local away_score=$4
    local home_team_id=${5:-1}
    local away_team_id=${6:-2}
    
    log "🤖 Getting ML prediction for match $match_id at minute $minute"
    
    activate_python
    
    # Generate ML prediction and capture output
    python3 -c "
import sys
import json
import asyncio
from pathlib import Path
sys.path.append('.')

from src.ml_models.prediction.api import predict_match_state, MatchState

async def get_prediction():
    try:
        match_state = MatchState(
            match_id=$match_id,
            minute=$minute,
            home_team_id=$home_team_id,
            away_team_id=$away_team_id,
            current_score_home=$home_score,
            current_score_away=$away_score
        )
        
        result = predict_match_state(match_state)
        
        # Extract key probabilities
        ml_predictions = {
            'match_id': $match_id,
            'minute': $minute,
            'probabilities': {
                'goal_next_1min': result.ensemble_prediction.get('goal_next_1min_any', 0.5),
                'goal_next_5min': result.ensemble_prediction.get('goal_next_5min_any', 0.5),
                'goal_next_15min': result.ensemble_prediction.get('goal_next_15min_any', 0.5)
            },
            'confidence': result.confidence_score,
            'processing_time_ms': result.processing_time_ms,
            'model_versions': len(result.model_versions),
            'timestamp': result.timestamp
        }
        
        # Save ML prediction
        output_file = Path('$REALTIME_DIR') / 'ml_predictions' / f'match_{$match_id}_minute_{$minute}.json'
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(ml_predictions, f, indent=2)
        
        print(json.dumps(ml_predictions))
        
    except Exception as e:
        error_prediction = {
            'match_id': $match_id,
            'minute': $minute,
            'error': str(e),
            'probabilities': {
                'goal_next_1min': 0.5,
                'goal_next_5min': 0.5,
                'goal_next_15min': 0.5
            },
            'confidence': 0.0
        }
        print(json.dumps(error_prediction))

asyncio.run(get_prediction())
" 2>/dev/null
}

# =============================================================================
# HISTORICAL ANALYSIS COMPONENT
# =============================================================================

get_historical_probabilities() {
    local match_id=$1
    local minute=$2
    local home_team=$3
    local away_team=$4
    local current_score_diff=$5
    
    log "📚 Calculating historical probabilities for $home_team vs $away_team"
    
    # Load historical context if available
    historical_file="$REALTIME_DIR/historical_context/match_${match_id}_context.json"
    
    if [ -f "$historical_file" ]; then
        python3 -c "
import json
import sys
from pathlib import Path

def calculate_historical_probabilities(context_file, minute, score_diff):
    '''Calculate probabilities based on historical performance'''
    
    try:
        with open(context_file, 'r') as f:
            context = json.load(f)
        
        home_analysis = context['home_team_analysis']
        away_analysis = context['away_team_analysis']
        
        # Base probabilities from historical data
        if minute >= 70:
            base_prob = (home_analysis['late_game_stats']['goals_after_70min'] + 
                        away_analysis['late_game_stats']['goals_after_70min']) / 2
        else:
            base_prob = (home_analysis['late_game_stats']['goals_after_60min'] + 
                        away_analysis['late_game_stats']['goals_after_60min']) / 2
        
        # Adjust for current game state
        if score_diff == 0:  # Tied game
            motivation_factor = 1.2  # Both teams motivated to score
        elif abs(score_diff) == 1:  # One goal difference
            motivation_factor = 1.1  # Losing team motivated, winning team defending
        else:  # Larger difference
            motivation_factor = 0.8  # Less urgency
        
        # Factor in recent form
        home_momentum = home_analysis['recent_form']['momentum_score']
        away_momentum = away_analysis['recent_form']['momentum_score']
        form_factor = (home_momentum + away_momentum) / 2
        
        # Calculate final historical probability
        historical_prob_1min = min(0.95, base_prob * 0.3 * motivation_factor * form_factor)
        historical_prob_5min = min(0.95, base_prob * 0.8 * motivation_factor * form_factor)
        historical_prob_15min = min(0.95, base_prob * 1.5 * motivation_factor * form_factor)
        
        historical_data = {
            'match_id': int('$match_id'),
            'minute': int('$minute'),
            'historical_probabilities': {
                'goal_next_1min': round(historical_prob_1min, 3),
                'goal_next_5min': round(historical_prob_5min, 3),
                'goal_next_15min': round(historical_prob_15min, 3)
            },
            'factors': {
                'base_probability': round(base_prob, 3),
                'motivation_factor': round(motivation_factor, 2),
                'form_factor': round(form_factor, 2),
                'home_momentum': round(home_momentum, 2),
                'away_momentum': round(away_momentum, 2)
            },
            'confidence': 0.7
        }
        
        return historical_data
        
    except Exception as e:
        return {
            'match_id': int('$match_id'),
            'minute': int('$minute'),
            'error': str(e),
            'historical_probabilities': {
                'goal_next_1min': 0.5,
                'goal_next_5min': 0.5,
                'goal_next_15min': 0.5
            },
            'confidence': 0.0
        }

# Calculate historical probabilities
result = calculate_historical_probabilities('$historical_file', $minute, $current_score_diff)

# Save historical analysis
output_file = Path('$REALTIME_DIR') / 'historical_predictions' / f'match_{$match_id}_minute_{$minute}.json'
output_file.parent.mkdir(exist_ok=True)

with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(json.dumps(result))
"
    else
        # Fallback historical analysis
        echo "{
            \"match_id\": $match_id,
            \"minute\": $minute,
            \"historical_probabilities\": {
                \"goal_next_1min\": 0.5,
                \"goal_next_5min\": 0.5,
                \"goal_next_15min\": 0.5
            },
            \"confidence\": 0.0,
            \"note\": \"No historical context available\"
        }"
    fi
}

# =============================================================================
# ENSEMBLE PROBABILITY CALCULATION
# =============================================================================

calculate_ensemble_probability() {
    local match_id=$1
    local minute=$2
    local home_team=$3
    local away_team=$4
    local home_score=$5
    local away_score=$6
    
    log "🎯 Calculating ensemble probability for match $match_id at minute $minute"
    
    # Calculate score difference
    score_diff=$((home_score - away_score))
    
    # Get ML prediction
    ml_result=$(get_ml_prediction "$match_id" "$minute" "$home_score" "$away_score")
    
    # Get historical probabilities
    historical_result=$(get_historical_probabilities "$match_id" "$minute" "$home_team" "$away_team" "$score_diff")
    
    # Combine predictions using weighted ensemble
    python3 -c "
import json
import sys
from datetime import datetime
from pathlib import Path

def combine_predictions(ml_json, historical_json, ml_weight=0.7, historical_weight=0.3):
    '''Combine ML and historical predictions with weights'''
    
    try:
        ml_data = json.loads('''$ml_result''')
        historical_data = json.loads('''$historical_result''')
        
        # Extract probabilities
        ml_probs = ml_data.get('probabilities', {})
        hist_probs = historical_data.get('historical_probabilities', {})
        
        # Calculate weighted ensemble
        ensemble_probs = {}
        for timeframe in ['goal_next_1min', 'goal_next_5min', 'goal_next_15min']:
            ml_prob = ml_probs.get(timeframe, 0.5)
            hist_prob = hist_probs.get(timeframe, 0.5)
            
            ensemble_prob = (ml_prob * ml_weight) + (hist_prob * historical_weight)
            ensemble_probs[timeframe] = round(ensemble_prob, 3)
        
        # Calculate combined confidence
        ml_confidence = ml_data.get('confidence', 0.0)
        hist_confidence = historical_data.get('confidence', 0.0)
        combined_confidence = (ml_confidence * ml_weight) + (hist_confidence * historical_weight)
        
        # Generate betting recommendations
        recommendations = generate_betting_recommendations(ensemble_probs, combined_confidence)
        
        ensemble_result = {
            'match_id': $match_id,
            'minute': $minute,
            'match_info': {
                'home_team': '$home_team',
                'away_team': '$away_team',
                'score': '$home_score-$away_score',
                'score_difference': $score_diff
            },
            'ensemble_probabilities': ensemble_probs,
            'confidence_score': round(combined_confidence, 3),
            'component_predictions': {
                'ml_prediction': ml_data,
                'historical_prediction': historical_data
            },
            'betting_recommendations': recommendations,
            'calculation_timestamp': datetime.now().isoformat(),
            'weights_used': {
                'ml_weight': ml_weight,
                'historical_weight': historical_weight
            }
        }
        
        return ensemble_result
        
    except Exception as e:
        return {
            'match_id': $match_id,
            'minute': $minute,
            'error': str(e),
            'ensemble_probabilities': {
                'goal_next_1min': 0.5,
                'goal_next_5min': 0.5,
                'goal_next_15min': 0.5
            },
            'confidence_score': 0.0
        }

def generate_betting_recommendations(probabilities, confidence):
    '''Generate betting recommendations based on probabilities'''
    
    recommendations = {
        'action': 'HOLD',
        'confidence_level': 'LOW',
        'recommended_bets': [],
        'avoid_bets': [],
        'reasoning': []
    }
    
    # High confidence thresholds
    HIGH_PROB_THRESHOLD = 0.7
    LOW_PROB_THRESHOLD = 0.3
    HIGH_CONFIDENCE_THRESHOLD = 0.6
    
    prob_1min = probabilities.get('goal_next_1min', 0.5)
    prob_5min = probabilities.get('goal_next_5min', 0.5)
    prob_15min = probabilities.get('goal_next_15min', 0.5)
    
    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        recommendations['confidence_level'] = 'HIGH'
        
        # High probability of goal in next 5-15 minutes
        if prob_15min >= HIGH_PROB_THRESHOLD:
            recommendations['action'] = 'BET'
            recommendations['recommended_bets'].append({
                'bet_type': 'Goal in next 15 minutes',
                'probability': prob_15min,
                'confidence': confidence,
                'timeframe': '15min'
            })
            recommendations['reasoning'].append(f'High probability ({prob_15min:.1%}) of goal in next 15 minutes')
        
        # Low probability - good for backing NO goals
        elif prob_15min <= LOW_PROB_THRESHOLD:
            recommendations['action'] = 'BET'
            recommendations['recommended_bets'].append({
                'bet_type': 'No goal in next 15 minutes',
                'probability': 1 - prob_15min,
                'confidence': confidence,
                'timeframe': '15min'
            })
            recommendations['reasoning'].append(f'Low probability ({prob_15min:.1%}) of goal in next 15 minutes')
        
        # Immediate goal opportunity
        if prob_1min >= HIGH_PROB_THRESHOLD:
            recommendations['recommended_bets'].append({
                'bet_type': 'Goal in next minute',
                'probability': prob_1min,
                'confidence': confidence,
                'timeframe': '1min',
                'urgency': 'IMMEDIATE'
            })
            recommendations['reasoning'].append(f'Immediate goal opportunity ({prob_1min:.1%})')
    
    elif confidence >= 0.4:
        recommendations['confidence_level'] = 'MEDIUM'
        
        # Medium confidence - more conservative approach
        if prob_15min >= 0.8:
            recommendations['action'] = 'CONSIDER'
            recommendations['recommended_bets'].append({
                'bet_type': 'Goal in next 15 minutes',
                'probability': prob_15min,
                'confidence': confidence,
                'timeframe': '15min',
                'note': 'Medium confidence - consider smaller stake'
            })
    
    else:
        recommendations['confidence_level'] = 'LOW'
        recommendations['action'] = 'HOLD'
        recommendations['reasoning'].append('Low confidence - avoid betting')
    
    # Always avoid betting if probabilities are in the uncertain range (0.4-0.6)
    uncertain_bets = []
    for timeframe, prob in [('1min', prob_1min), ('5min', prob_5min), ('15min', prob_15min)]:
        if 0.4 <= prob <= 0.6:
            uncertain_bets.append(f'{timeframe} goal betting')
    
    if uncertain_bets:
        recommendations['avoid_bets'].extend(uncertain_bets)
        recommendations['reasoning'].append('Avoid betting in uncertain probability ranges')
    
    return recommendations

# Calculate ensemble prediction
result = combine_predictions('$ml_result', '$historical_result', $ML_WEIGHT, $HISTORICAL_WEIGHT)

# Save ensemble result
output_file = Path('$REALTIME_DIR') / 'ensemble_predictions' / f'match_{$match_id}_minute_{$minute}.json'
output_file.parent.mkdir(exist_ok=True)

with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
"
    
    log "✅ Ensemble probability calculated and saved"
}

# =============================================================================
# BETTING RECOMMENDATION GENERATOR
# =============================================================================

generate_betting_report() {
    local match_id=$1
    local minute=$2
    
    log "📊 Generating betting report for match $match_id"
    
    ensemble_file="$REALTIME_DIR/ensemble_predictions/match_${match_id}_minute_${minute}.json"
    
    if [ -f "$ensemble_file" ]; then
        # Generate human-readable report
        python3 -c "
import json
from pathlib import Path

def format_betting_report(ensemble_file):
    with open(ensemble_file, 'r') as f:
        data = json.load(f)
    
    if 'error' in data:
        return f'Error generating report: {data[\"error\"]}'
    
    match_info = data['match_info']
    probs = data['ensemble_probabilities']
    recommendations = data['betting_recommendations']
    confidence = data['confidence_score']
    
    report = f'''
🏈 MATCH ANALYSIS REPORT
========================
Match: {match_info['home_team']} vs {match_info['away_team']}
Current Score: {match_info['score']}
Minute: {data['minute']}
Analysis Time: {data['calculation_timestamp'][:19]}

📊 GOAL PROBABILITIES
=====================
Next 1 minute:  {probs['goal_next_1min']:.1%}
Next 5 minutes: {probs['goal_next_5min']:.1%}  
Next 15 minutes: {probs['goal_next_15min']:.1%}

Confidence Level: {confidence:.1%} ({recommendations['confidence_level']})

🎯 BETTING RECOMMENDATIONS
==========================
Action: {recommendations['action']}
'''
    
    if recommendations['recommended_bets']:
        report += '\n✅ RECOMMENDED BETS:\n'
        for bet in recommendations['recommended_bets']:
            urgency = bet.get('urgency', '')
            urgency_text = f' [{urgency}]' if urgency else ''
            report += f'  • {bet[\"bet_type\"]} - {bet[\"probability\"]:.1%}{urgency_text}\n'
    
    if recommendations['avoid_bets']:
        report += '\n❌ AVOID THESE BETS:\n'
        for bet in recommendations['avoid_bets']:
            report += f'  • {bet}\n'
    
    if recommendations['reasoning']:
        report += '\n💡 REASONING:\n'
        for reason in recommendations['reasoning']:
            report += f'  • {reason}\n'
    
    report += '\n' + '='*50 + '\n'
    
    return report

report = format_betting_report('$ensemble_file')
print(report)

# Save formatted report
report_file = Path('$REALTIME_DIR') / 'reports' / f'betting_report_match_{$match_id}_minute_{$minute}.txt'
report_file.parent.mkdir(exist_ok=True)

with open(report_file, 'w') as f:
    f.write(report)

print(f'Report saved to: {report_file}')
"
    else
        log "❌ No ensemble prediction file found for match $match_id at minute $minute"
        return 1
    fi
}

# =============================================================================
# MAIN CALCULATION FUNCTION
# =============================================================================

main() {
    local match_id=$1
    local minute=$2
    local home_team=$3
    local away_team=$4
    local home_score=$5
    local away_score=$6
    
    # Validate inputs
    if [ -z "$match_id" ] || [ -z "$minute" ]; then
        log "❌ Error: match_id and minute are required"
        echo "Usage: $0 <match_id> <minute> [home_team] [away_team] [home_score] [away_score]"
        exit 1
    fi
    
    # Set defaults if not provided
    home_team=${home_team:-"Team A"}
    away_team=${away_team:-"Team B"}
    home_score=${home_score:-0}
    away_score=${away_score:-0}
    
    log "🚀 Starting probability calculation for match $match_id at minute $minute"
    log "   Teams: $home_team vs $away_team"
    log "   Score: $home_score-$away_score"
    
    # Create output directories
    mkdir -p "$REALTIME_DIR"/{ml_predictions,historical_predictions,ensemble_predictions,reports}
    
    # Calculate ensemble probability
    ensemble_result=$(calculate_ensemble_probability "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score")
    
    if [ $? -eq 0 ]; then
        log "✅ Ensemble probability calculation completed"
        
        # Generate betting report
        generate_betting_report "$match_id" "$minute"
        
        # Display key results
        echo "$ensemble_result" | python3 -c "
import json
import sys

try:
    data = json.load(sys.stdin)
    print(f'\\n🎯 QUICK RESULTS:')
    print(f'Match {data[\"match_id\"]}: {data[\"match_info\"][\"home_team\"]} vs {data[\"match_info\"][\"away_team\"]}')
    print(f'Goal probability (15min): {data[\"ensemble_probabilities\"][\"goal_next_15min\"]:.1%}')
    print(f'Confidence: {data[\"confidence_score\"]:.1%}')
    print(f'Recommendation: {data[\"betting_recommendations\"][\"action\"]}')
except:
    print('Error displaying results')
"
        
        log "✅ Probability calculation completed successfully"
    else
        log "❌ Probability calculation failed"
        exit 1
    fi
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Run main function with provided arguments
main "$@"