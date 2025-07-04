#!/bin/bash
# scripts/live_data_monitor.sh
# Continuously monitors live matches and captures data at key moments

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE7_HOME="$(dirname "$SCRIPT_DIR")"
source "$STAGE7_HOME/config/stage7_config.sh"

# Monitoring settings
POLL_INTERVAL=30  # Check every 30 seconds
KEY_MINUTES=(59 60 69 70 79 80)  # Critical minutes to capture
MAX_RETRIES=3

# =============================================================================
# LOGGING AND UTILITIES
# =============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [LIVE_MONITOR] $1" | tee -a "$LOGS_DIR/live_monitor.log"
}

activate_python() {
    if [ -f "$PYTHON_ENV/bin/activate" ]; then
        source "$PYTHON_ENV/bin/activate"
    fi
}

# =============================================================================
# LIVE MATCH DISCOVERY
# =============================================================================

discover_live_matches() {
    log "🔍 Discovering live matches..."
    
    activate_python
    
    # Use existing ML pipeline to get live matches
    python3 -c "
import asyncio
import json
import sys
sys.path.append('.')

async def get_live_matches():
    try:
        # Simulate getting live matches (replace with actual SofaScore API call)
        live_matches = [
            {'match_id': 12345, 'minute': 65, 'home_team': 'Arsenal', 'away_team': 'Chelsea', 'home_score': 1, 'away_score': 0},
            {'match_id': 12346, 'minute': 72, 'home_team': 'Liverpool', 'away_team': 'Man City', 'home_score': 2, 'away_score': 1},
            {'match_id': 12347, 'minute': 58, 'home_team': 'Barcelona', 'away_team': 'Real Madrid', 'home_score': 0, 'away_score': 0}
        ]
        
        # Filter for matches in interesting time periods (55+ minutes)
        interesting_matches = [m for m in live_matches if m['minute'] >= 55]
        
        with open('$REALTIME_DIR/live_matches.json', 'w') as f:
            json.dump(interesting_matches, f, indent=2)
        
        print(f'Found {len(interesting_matches)} interesting live matches')
        return interesting_matches
        
    except Exception as e:
        print(f'Error discovering matches: {e}')
        return []

if __name__ == '__main__':
    matches = asyncio.run(get_live_matches())
    for match in matches:
        print(f\"Match {match['match_id']}: {match['home_team']} vs {match['away_team']} - {match['minute']}'\")" > /tmp/discover_matches.py
    
    python3 /tmp/discover_matches.py
    rm /tmp/discover_matches.py
}

# =============================================================================
# DATA CAPTURE FOR KEY MINUTES
# =============================================================================

capture_match_snapshot() {
    local match_id=$1
    local current_minute=$2
    local home_team=$3
    local away_team=$4
    local home_score=$5
    local away_score=$6
    
    log "📸 Capturing snapshot for match $match_id at minute $current_minute"
    
    # Create snapshot directory
    snapshot_dir="$REALTIME_DIR/snapshots/match_${match_id}"
    mkdir -p "$snapshot_dir"
    
    # Capture current match state
    cat > "$snapshot_dir/minute_${current_minute}.json" << EOF
{
    "match_id": $match_id,
    "minute": $current_minute,
    "home_team": "$home_team",
    "away_team": "$away_team",
    "home_score": $home_score,
    "away_score": $away_score,
    "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "snapshot_type": "key_minute",
    "captured_by": "live_data_monitor"
}
EOF

    # Generate real-time prediction
    activate_python
    
    python3 -c "
import sys
sys.path.append('.')
import asyncio
from src.ml_models.cli_commands import run_ml_prediction

async def predict_match_state():
    try:
        success = await run_ml_prediction(
            match_id=$match_id,
            minute=$current_minute,
            home_score=$home_score,
            away_score=$away_score
        )
        
        if success:
            print('Prediction generated successfully')
        else:
            print('Prediction failed')
            
    except Exception as e:
        print(f'Error generating prediction: {e}')

if __name__ == '__main__':
    asyncio.run(predict_match_state())" > "$snapshot_dir/prediction_minute_${current_minute}.log" 2>&1
    
    log "✅ Snapshot captured for match $match_id at minute $current_minute"
}

# =============================================================================
# HISTORICAL DATA INTEGRATION
# =============================================================================

update_historical_context() {
    local match_id=$1
    local home_team=$2
    local away_team=$3
    
    log "📚 Updating historical context for $home_team vs $away_team"
    
    activate_python
    
    # Generate historical analysis
    python3 -c "
import json
import sys
from pathlib import Path

def analyze_team_history(team_name, opponent_name):
    '''Analyze team's historical performance in late-game situations'''
    
    # Simulate historical analysis (replace with actual database queries)
    historical_data = {
        'team': team_name,
        'opponent': opponent_name,
        'late_game_stats': {
            'goals_after_60min': 0.3,  # Average goals scored after 60th minute
            'goals_after_70min': 0.15, # Average goals scored after 70th minute
            'comeback_rate': 0.12,     # Rate of comebacks when losing
            'hold_lead_rate': 0.78,    # Rate of holding leads after 60min
            'total_matches_analyzed': 50
        },
        'recent_form': {
            'last_5_matches_goals_late': 2,
            'last_5_matches_conceded_late': 1,
            'momentum_score': 0.6  # 0-1 scale
        },
        'head_to_head': {
            'meetings_last_year': 2,
            'goals_in_late_periods': 1,
            'avg_total_goals': 2.5
        }
    }
    
    return historical_data

# Analyze both teams
home_analysis = analyze_team_history('$home_team', '$away_team')
away_analysis = analyze_team_history('$away_team', '$home_team')

historical_context = {
    'match_id': $match_id,
    'analysis_timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'home_team_analysis': home_analysis,
    'away_team_analysis': away_analysis,
    'combined_insights': {
        'expected_late_goals': home_analysis['late_game_stats']['goals_after_60min'] + away_analysis['late_game_stats']['goals_after_60min'],
        'high_probability_team': 'home' if home_analysis['recent_form']['momentum_score'] > away_analysis['recent_form']['momentum_score'] else 'away',
        'confidence_level': 0.7
    }
}

# Save historical context
output_file = Path('$REALTIME_DIR') / 'historical_context' / f'match_{$match_id}_context.json'
output_file.parent.mkdir(exist_ok=True)

with open(output_file, 'w') as f:
    json.dump(historical_context, f, indent=2)

print(f'Historical context saved to {output_file}')
"
    
    log "✅ Historical context updated for match $match_id"
}

# =============================================================================
# MAIN MONITORING LOOP
# =============================================================================

main_monitoring_loop() {
    log "🔄 Starting main monitoring loop (poll interval: ${POLL_INTERVAL}s)"
    
    while true; do
        # Discover currently live matches
        discover_live_matches
        
        # Check if we have live matches to monitor
        if [ -f "$REALTIME_DIR/live_matches.json" ]; then
            # Process each live match
            python3 -c "
import json
import sys

try:
    with open('$REALTIME_DIR/live_matches.json', 'r') as f:
        matches = json.load(f)
    
    for match in matches:
        match_id = match['match_id']
        minute = match['minute']
        home_team = match['home_team']
        away_team = match['away_team']
        home_score = match['home_score']
        away_score = match['away_score']
        
        # Check if this is a key minute
        key_minutes = [59, 60, 69, 70, 79, 80]
        if minute in key_minutes:
            print(f'KEY_MINUTE:{match_id}:{minute}:{home_team}:{away_team}:{home_score}:{away_score}')
        else:
            print(f'REGULAR:{match_id}:{minute}:{home_team}:{away_team}:{home_score}:{away_score}')
            
except Exception as e:
    print(f'ERROR:Could not process live matches: {e}')
" | while IFS=':' read -r type match_id minute home_team away_team home_score away_score; do
                case $type in
                    KEY_MINUTE)
                        log "🎯 Key minute detected: Match $match_id at minute $minute"
                        capture_match_snapshot "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score"
                        update_historical_context "$match_id" "$home_team" "$away_team"
                        
                        # Trigger immediate probability calculation
                        bash "$STAGE7_HOME/scripts/calculate_probabilities.sh" "$match_id" "$minute" &
                        ;;
                    REGULAR)
                        log "📊 Monitoring: Match $match_id at minute $minute ($home_team $home_score-$away_score $away_team)"
                        ;;
                    ERROR)
                        log "❌ Error: $match_id"
                        ;;
                esac
            done
        else
            log "📭 No live matches file found"
        fi
        
        # Wait before next poll
        sleep $POLL_INTERVAL
    done
}

# =============================================================================
# CLEANUP AND ERROR HANDLING
# =============================================================================

cleanup() {
    log "🧹 Cleaning up live data monitor..."
    
    # Remove any temporary files
    rm -f /tmp/discover_matches.py
    
    # Archive old snapshots (keep last 24 hours)
    find "$REALTIME_DIR/snapshots" -type f -mtime +1 -delete 2>/dev/null || true
    
    log "✅ Cleanup completed"
}

# Trap signals for clean shutdown
trap cleanup EXIT INT TERM

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Ensure required directories exist
mkdir -p "$REALTIME_DIR"/{snapshots,historical_context}
mkdir -p "$STAGE7_HOME/pids"

# Start monitoring
log "🚀 Live Data Monitor starting..."
main_monitoring_loop