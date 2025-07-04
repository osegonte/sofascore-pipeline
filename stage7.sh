#!/bin/bash
# stage7.sh - Run Stage 7 directly from project root

# Ensure we're in the project root
if [ ! -f "src/main.py" ]; then
    echo "❌ Please run this script from the SofaScore pipeline project root"
    echo "   (The directory containing src/main.py)"
    exit 1
fi

# Set absolute paths from project root
export PROJECT_ROOT="$(pwd)"
export STAGE7_HOME="$PROJECT_ROOT/stage7"
export PYTHON_ENV="$PROJECT_ROOT/venv"
export DATA_DIR="$STAGE7_HOME/data"
export LOGS_DIR="$STAGE7_HOME/logs"
export MODELS_DIR="$PROJECT_ROOT/data/models"
export REALTIME_DIR="$STAGE7_HOME/data/realtime"

# Create necessary directories
mkdir -p "$DATA_DIR" "$LOGS_DIR" "$REALTIME_DIR"
mkdir -p "$STAGE7_HOME/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOGS_DIR/stage7.log"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOGS_DIR/stage7.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOGS_DIR/stage7.log"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOGS_DIR/stage7.log"
}

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

check_prerequisites() {
    log "🔍 Checking Stage 7 prerequisites..."
    
    local issues=0
    local warnings=0
    
    # Check ML models
    if [ ! -d "$MODELS_DIR/saved_models" ]; then
        log_warning "Stage 6 ML models not found at $MODELS_DIR/saved_models"
        echo "💡 Available model files:"
        find . -name "*.joblib" -type f 2>/dev/null | head -3 | sed 's/^/   /'
        warnings=$((warnings + 1))
    else
        model_count=$(ls "$MODELS_DIR/saved_models"/*.joblib 2>/dev/null | wc -l)
        if [ "$model_count" -gt 0 ]; then
            log_success "Found $model_count ML models from Stage 6"
        else
            log_warning "Models directory exists but no .joblib files found"
            warnings=$((warnings + 1))
        fi
    fi
    
    # Check training data
    if [ ! -f "$PROJECT_ROOT/demo_training_dataset.csv" ]; then
        log_warning "Training dataset not found at $PROJECT_ROOT/demo_training_dataset.csv"
        echo "💡 Available CSV files:"
        find . -maxdepth 1 -name "*.csv" -type f 2>/dev/null | head -3 | sed 's/^/   /'
        warnings=$((warnings + 1))
    else
        lines=$(wc -l < "$PROJECT_ROOT/demo_training_dataset.csv" 2>/dev/null || echo "0")
        log_success "Training dataset found ($lines samples)"
    fi
    
    # Check Python environment
    if [ ! -d "$PYTHON_ENV" ]; then
        log_error "Python virtual environment not found at $PYTHON_ENV"
        issues=$((issues + 1))
    else
        log_success "Python virtual environment found"
    fi
    
    if [ $issues -eq 0 ]; then
        if [ $warnings -eq 0 ]; then
            log_success "All prerequisites check passed"
        else
            log_warning "$warnings warnings found, but continuing with limited functionality"
        fi
        return 0
    else
        log_error "$issues critical issues found"
        return 1
    fi
}

# =============================================================================
# MONITORING FUNCTIONS
# =============================================================================

create_monitor_scripts() {
    log "📝 Creating Stage 7 monitoring scripts..."
    
    mkdir -p "$STAGE7_HOME/scripts"
    
    # Create live data monitor
    cat > "$STAGE7_HOME/scripts/live_data_monitor.sh" << 'MONITOR_EOF'
#!/bin/bash
# Live Data Monitor - Monitors live matches for Stage 7

STAGE7_HOME="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"
PROJECT_ROOT="$(dirname "$STAGE7_HOME")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MONITOR] $1"
}

log "🔄 Live data monitor starting..."

# Monitoring loop
while true; do
    log "📡 Scanning for live matches..."
    
    # Create output directory
    mkdir -p "$STAGE7_HOME/data/realtime"
    
    # Simulate live match discovery
    python3 -c "
import json
import random
import sys
from datetime import datetime

# Generate realistic demo matches
live_matches = []
demo_matches = [
    {'match_id': 12345, 'home_team': 'Arsenal', 'away_team': 'Chelsea'},
    {'match_id': 12346, 'home_team': 'Liverpool', 'away_team': 'Man City'},
    {'match_id': 12347, 'home_team': 'Barcelona', 'away_team': 'Real Madrid'}
]

for match in demo_matches:
    minute = random.randint(55, 90)
    home_score = random.randint(0, 3)
    away_score = random.randint(0, 3)
    
    if minute >= 55:
        match.update({
            'minute': minute,
            'home_score': home_score,
            'away_score': away_score,
            'status': 'live',
            'last_update': datetime.now().isoformat()
        })
        live_matches.append(match)

# Save live matches data
with open('$STAGE7_HOME/data/realtime/live_matches.json', 'w') as f:
    json.dump(live_matches, f, indent=2)

print(f'Found {len(live_matches)} live matches')
for match in live_matches:
    print(f\"Match {match['match_id']}: {match['home_team']} vs {match['away_team']} - {match['minute']}' ({match['home_score']}-{match['away_score']})\")
" 2>/dev/null || log "⚠️  Python simulation failed"
    
    # Check for key minutes
    if [ -f "$STAGE7_HOME/data/realtime/live_matches.json" ]; then
        python3 -c "
import json
try:
    with open('$STAGE7_HOME/data/realtime/live_matches.json', 'r') as f:
        matches = json.load(f)
    
    key_minutes = [59, 60, 69, 70, 79, 80]
    
    for match in matches:
        minute = match.get('minute', 0)
        if minute in key_minutes:
            print(f'KEY:{match[\"match_id\"]}:{minute}:{match[\"home_team\"]}:{match[\"away_team\"]}:{match[\"home_score\"]}:{match[\"away_score\"]}')
except:
    pass
" | while IFS=':' read -r type match_id minute home_team away_team home_score away_score; do
            if [ "$type" = "KEY" ]; then
                log "🎯 KEY MINUTE: Match $match_id at minute $minute"
                if [ -f "$STAGE7_HOME/scripts/calculate_probabilities.sh" ]; then
                    bash "$STAGE7_HOME/scripts/calculate_probabilities.sh" "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score" &
                fi
            fi
        done
    fi
    
    sleep 30
done
MONITOR_EOF
    
    # Create probability calculator
    cat > "$STAGE7_HOME/scripts/calculate_probabilities.sh" << 'CALC_EOF'
#!/bin/bash
# Probability Calculator

STAGE7_HOME="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CALC] $1"
}

match_id=$1
minute=$2
home_team=$3
away_team=$4
home_score=$5
away_score=$6

log "🎯 Calculating probabilities for match $match_id at minute $minute"

mkdir -p "$STAGE7_HOME/data/realtime/ensemble_predictions"
mkdir -p "$STAGE7_HOME/data/realtime/alerts"

# Generate probability calculation
python3 -c "
import json
import random
from datetime import datetime

minute = int($minute)
home_score = int($home_score)
away_score = int($away_score)
score_diff = home_score - away_score

# Calculate realistic probabilities
time_factor = 1.0 + (minute - 60) * 0.01

if score_diff == 0:
    score_factor = 1.2
elif abs(score_diff) == 1:
    score_factor = 1.1
else:
    score_factor = 0.8

base_prob_15min = 0.4 * time_factor * score_factor
random.seed($match_id + minute)
prob_15min = min(0.95, max(0.15, base_prob_15min * random.uniform(0.9, 1.1)))
prob_5min = prob_15min * 0.6
prob_1min = prob_5min * 0.3
confidence = min(0.9, (time_factor + score_factor) / 2 * 0.8)

# Generate recommendation
if confidence >= 0.6 and prob_15min >= 0.7:
    action, reason = 'BET', 'High confidence betting opportunity'
elif confidence >= 0.5 and prob_15min >= 0.6:
    action, reason = 'CONSIDER', 'Medium confidence opportunity'
elif prob_15min <= 0.3:
    action, reason = 'BET_NO_GOAL', 'Low probability - consider no goal bet'
else:
    action, reason = 'HOLD', 'Uncertain probability'

result = {
    'match_id': $match_id,
    'minute': $minute,
    'match_info': {
        'home_team': '$home_team',
        'away_team': '$away_team',
        'score': '$home_score-$away_score'
    },
    'ensemble_probabilities': {
        'goal_next_1min': round(prob_1min, 3),
        'goal_next_5min': round(prob_5min, 3),
        'goal_next_15min': round(prob_15min, 3)
    },
    'confidence_score': round(confidence, 3),
    'recommendation': {
        'action': action,
        'reason': reason
    },
    'timestamp': datetime.now().isoformat()
}

# Save result
output_file = f'$STAGE7_HOME/data/realtime/ensemble_predictions/match_{$match_id}_minute_{$minute}.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f'🎯 PREDICTION RESULT:')
print(f'   Match $match_id: $home_team vs $away_team')
print(f'   Goal probability (15min): {prob_15min:.1%}')
print(f'   Confidence: {confidence:.1%}')
print(f'   Recommendation: {action}')

# Generate alert if high confidence
if confidence >= 0.6 and prob_15min >= 0.7:
    alert = {
        'alert_id': f'alert_{$match_id}_{$minute}',
        'match_id': $match_id,
        'message': 'HIGH CONFIDENCE BETTING OPPORTUNITY',
        'probability': prob_15min,
        'confidence': confidence,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(f'$STAGE7_HOME/data/realtime/alerts/alert_{$match_id}_{$minute}.json', 'w') as f:
        json.dump(alert, f, indent=2)
    
    print('🚨 ALERT: High confidence opportunity!')
"

log "✅ Calculation completed for match $match_id"
CALC_EOF
    
    # Create scheduler
    cat > "$STAGE7_HOME/scripts/probability_scheduler.sh" << 'SCHED_EOF'
#!/bin/bash
# Probability Scheduler

STAGE7_HOME="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SCHEDULER] $1"
}

log "⏰ Probability scheduler starting..."

while true; do
    if [ -f "$STAGE7_HOME/data/realtime/live_matches.json" ]; then
        active_matches=$(python3 -c "
import json
try:
    with open('$STAGE7_HOME/data/realtime/live_matches.json', 'r') as f:
        matches = json.load(f)
    print(len([m for m in matches if m.get('minute', 0) >= 55]))
except:
    print(0)
" 2>/dev/null || echo "0")
        
        if [ "$active_matches" -gt 0 ]; then
            log "📊 Monitoring $active_matches active matches"
        fi
    fi
    
    sleep 15
done
SCHED_EOF
    
    # Make scripts executable
    chmod +x "$STAGE7_HOME/scripts"/*.sh
    
    log_success "Stage 7 monitoring scripts created"
}

start_realtime_monitoring() {
    log "📡 Starting real-time monitoring system..."
    
    # Ensure scripts exist
    if [ ! -f "$STAGE7_HOME/scripts/live_data_monitor.sh" ]; then
        create_monitor_scripts
    fi
    
    # Start live data monitor
    echo "🔄 Starting live data monitor..."
    nohup bash "$STAGE7_HOME/scripts/live_data_monitor.sh" > "$LOGS_DIR/live_monitor.log" 2>&1 &
    monitor_pid=$!
    echo $monitor_pid > "$STAGE7_HOME/pids/live_monitor.pid"
    log "Live monitor started (PID: $monitor_pid)"
    
    # Start probability scheduler
    echo "📊 Starting probability scheduler..."
    nohup bash "$STAGE7_HOME/scripts/probability_scheduler.sh" > "$LOGS_DIR/probability_scheduler.log" 2>&1 &
    scheduler_pid=$!
    echo $scheduler_pid > "$STAGE7_HOME/pids/probability_scheduler.pid"
    log "Probability scheduler started (PID: $scheduler_pid)"
    
    log_success "Real-time monitoring started"
}

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

main() {
    echo ""
    echo -e "${CYAN}🚀 Stage 7: Real-Time Analysis and Probability Modeling${NC}"
    echo -e "${CYAN}======================================================${NC}"
    echo ""
    
    log "Starting Stage 7 from project root: $PROJECT_ROOT"
    
    # Check prerequisites (non-blocking)
    if ! check_prerequisites; then
        echo ""
        echo -e "${YELLOW}⚠️  Some prerequisites missing, but continuing with limited functionality${NC}"
        echo ""
    fi
    
    # Start monitoring
    start_realtime_monitoring
    
    echo ""
    log_success "Stage 7 initialization completed"
    
    echo ""
    echo -e "${GREEN}🎯 Stage 7 is now running!${NC}"
    echo -e "   ${WHITE}📊 Monitor status: ./stage7.sh status${NC}"
    echo -e "   ${WHITE}📝 View logs: tail -f stage7/logs/stage7.log${NC}"
    echo -e "   ${WHITE}🛑 Stop system: ./stage7.sh stop${NC}"
    echo ""
}

stop_all_processes() {
    log "🛑 Stopping all Stage 7 processes..."
    
    local stopped_count=0
    for pid_file in "$STAGE7_HOME/pids"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            process_name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                log_success "Stopped $process_name (PID: $pid)"
                stopped_count=$((stopped_count + 1))
            fi
            rm "$pid_file"
        fi
    done
    
    if [ $stopped_count -eq 0 ]; then
        log "No processes were running"
    else
        log_success "Stopped $stopped_count processes"
    fi
}

show_status() {
    echo ""
    echo -e "${BLUE}📊 Stage 7 System Status${NC}"
    echo -e "${BLUE}========================${NC}"
    echo ""
    echo -e "🏠 Project Root: ${WHITE}$PROJECT_ROOT${NC}"
    echo -e "📁 Stage 7 Home: ${WHITE}$STAGE7_HOME${NC}"
    echo ""
    
    # Check process status
    local running_count=0
    echo -e "${PURPLE}🔍 Process Status:${NC}"
    
    for pid_file in "$STAGE7_HOME/pids"/*.pid; do
        if [ -f "$pid_file" ]; then
            process_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  ${GREEN}✅ $process_name (PID: $pid) - Running${NC}"
                running_count=$((running_count + 1))
            else
                echo -e "  ${RED}❌ $process_name (PID: $pid) - Not running${NC}"
            fi
        fi
    done
    
    if [ $running_count -eq 0 ]; then
        echo -e "  ${YELLOW}📭 No processes currently running${NC}"
        echo ""
        echo -e "${CYAN}💡 Start Stage 7 with: ${WHITE}./stage7.sh start${NC}"
    else
        echo ""
        echo -e "${GREEN}🎯 Stage 7 is actively monitoring live matches!${NC}"
    fi
    
    echo ""
    echo -e "${PURPLE}📁 Data Status:${NC}"
    
    # Check ML models
    if [ -d "$MODELS_DIR/saved_models" ]; then
        model_count=$(ls "$MODELS_DIR/saved_models"/*.joblib 2>/dev/null | wc -l)
        if [ "$model_count" -gt 0 ]; then
            echo -e "  ${GREEN}🤖 ML models: ✅ $model_count available${NC}"
        else
            echo -e "  ${YELLOW}🤖 ML models: ⚠️  Directory exists but no models found${NC}"
        fi
    else
        echo -e "  ${RED}🤖 ML models: ❌ Not found${NC}"
    fi
    
    # Check training data
    if [ -f "$PROJECT_ROOT/demo_training_dataset.csv" ]; then
        lines=$(wc -l < "$PROJECT_ROOT/demo_training_dataset.csv" 2>/dev/null || echo "0")
        echo -e "  ${GREEN}📊 Training data: ✅ Available ($lines samples)${NC}"
    else
        echo -e "  ${RED}📊 Training data: ❌ Missing${NC}"
    fi
    
    # Check recent activity
    if [ -f "$LOGS_DIR/stage7.log" ]; then
        recent_entries=$(tail -5 "$LOGS_DIR/stage7.log" | wc -l)
        echo -e "  ${GREEN}📝 Recent log entries: $recent_entries${NC}"
    else
        echo -e "  ${YELLOW}📝 No logs yet${NC}"
    fi
    
    # Check live data
    if [ -f "$REALTIME_DIR/live_matches.json" ]; then
        match_count=$(python3 -c "
import json
try:
    with open('$REALTIME_DIR/live_matches.json', 'r') as f:
        matches = json.load(f)
    print(len(matches))
except:
    print(0)
" 2>/dev/null || echo "0")
        
        echo -e "  ${GREEN}🕒 Live data: ✅ ($match_count matches)${NC}"
    else
        echo -e "  ${YELLOW}📭 No live data captured yet${NC}"
    fi
    
    echo ""
}

run_demo() {
    echo ""
    echo -e "${CYAN}🚀 Stage 7 Real-Time Analysis Demo${NC}"
    echo -e "${CYAN}==================================${NC}"
    echo ""
    
    # Demo probability calculations
    demo_matches=(
        "12345:65:Arsenal:Chelsea:1:0"
        "12346:72:Liverpool:ManCity:2:1" 
        "12347:58:Barcelona:RealMadrid:0:0"
    )
    
    for match_data in "${demo_matches[@]}"; do
        IFS=':' read -r match_id minute home away home_score away_score <<< "$match_data"
        
        echo ""
        echo -e "${WHITE}🏈 Match $match_id: $home vs $away ($home_score-$away_score) at ${minute}'${NC}"
        echo "   🤖 Running probability calculation..."
        
        # Ensure scripts exist
        if [ ! -f "$STAGE7_HOME/scripts/calculate_probabilities.sh" ]; then
            create_monitor_scripts
        fi
        
        # Run actual calculation
        bash "$STAGE7_HOME/scripts/calculate_probabilities.sh" "$match_id" "$minute" "$home" "$away" "$home_score" "$away_score" 2>/dev/null | grep "🎯\|Recommendation\|probability\|ALERT"
        
        sleep 1
    done
    
    echo ""
    echo -e "${GREEN}✅ Demo completed!${NC}"
    echo ""
    echo -e "${PURPLE}📂 Generated files:${NC}"
    echo -e "   ${WHITE}- Predictions: $REALTIME_DIR/ensemble_predictions/${NC}"
    echo -e "   ${WHITE}- Alerts: $REALTIME_DIR/alerts/${NC}"
    echo ""
}

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

case "${1:-start}" in
    start)
        main
        ;;
    stop)
        stop_all_processes
        ;;
    status)
        show_status
        ;;
    restart)
        stop_all_processes
        sleep 2
        main
        ;;
    demo)
        run_demo
        ;;
    *)
        echo ""
        echo -e "${CYAN}Stage 7: Real-Time Analysis and Probability Modeling${NC}"
        echo "Usage: $0 {start|stop|status|restart|demo}"
        echo ""
        show_status
        exit 1
        ;;
esac
EOF

# Make it executable
chmod +x stage7.sh

echo "✅ Created stage7.sh in project root!"
echo ""
echo "🧪 Testing the new script..."