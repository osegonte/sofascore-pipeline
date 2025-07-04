#!/bin/bash
# config/stage7_config.sh
# Configuration file for Stage 7 Real-Time Analysis

# =============================================================================
# DIRECTORY STRUCTURE
# =============================================================================

# Base directories
export STAGE7_HOME="${STAGE7_HOME:-$(pwd)}"
export PYTHON_ENV="${STAGE7_HOME}/venv"
export DATA_DIR="${STAGE7_HOME}/data"
export LOGS_DIR="${STAGE7_HOME}/logs"
export MODELS_DIR="${STAGE7_HOME}/data/models"
export REALTIME_DIR="${STAGE7_HOME}/data/realtime"

# Create directory structure
mkdir -p "$DATA_DIR"/{historical,realtime,models}
mkdir -p "$REALTIME_DIR"/{snapshots,historical_context,ml_predictions,historical_predictions,ensemble_predictions,reports}
mkdir -p "$LOGS_DIR"
mkdir -p "$STAGE7_HOME"/{scripts,config,pids}

# =============================================================================
# MONITORING SETTINGS
# =============================================================================

# Polling intervals (seconds)
export LIVE_POLL_INTERVAL=30
export PROBABILITY_CALC_INTERVAL=60
export HISTORICAL_UPDATE_INTERVAL=300

# Key minutes for enhanced monitoring
export KEY_MINUTES="59 60 69 70 79 80"

# Match filtering
export MIN_MINUTE_THRESHOLD=55  # Only monitor matches after 55th minute
export MAX_MINUTE_THRESHOLD=95  # Stop monitoring after 95th minute

# =============================================================================
# PROBABILITY CALCULATION SETTINGS
# =============================================================================

# Ensemble weights
export ML_WEIGHT=0.7
export HISTORICAL_WEIGHT=0.3

# Confidence thresholds
export HIGH_CONFIDENCE_THRESHOLD=0.6
export MEDIUM_CONFIDENCE_THRESHOLD=0.4
export LOW_CONFIDENCE_THRESHOLD=0.2

# Probability thresholds for betting recommendations
export HIGH_PROB_THRESHOLD=0.7
export LOW_PROB_THRESHOLD=0.3
export UNCERTAIN_RANGE_MIN=0.4
export UNCERTAIN_RANGE_MAX=0.6

# =============================================================================
# HISTORICAL ANALYSIS SETTINGS
# =============================================================================

# Historical data parameters
export HISTORICAL_LOOKBACK_MONTHS=12
export MIN_HISTORICAL_MATCHES=10
export HEAD_TO_HEAD_LOOKBACK_MONTHS=24

# Team form analysis
export RECENT_FORM_MATCHES=5
export MOMENTUM_DECAY_FACTOR=0.8

# =============================================================================
# BETTING RECOMMENDATION SETTINGS
# =============================================================================

# Risk levels
export CONSERVATIVE_MODE=false
export AGGRESSIVE_MODE=false
export BALANCED_MODE=true

# Stake recommendations (as percentage of bankroll)
export HIGH_CONFIDENCE_STAKE=5.0
export MEDIUM_CONFIDENCE_STAKE=2.0
export LOW_CONFIDENCE_STAKE=1.0

# Betting timeframes
export IMMEDIATE_TIMEFRAME=1    # 1 minute
export SHORT_TIMEFRAME=5        # 5 minutes  
export MEDIUM_TIMEFRAME=15      # 15 minutes

# =============================================================================
# API AND DATA SOURCE SETTINGS
# =============================================================================

# SofaScore API settings
export SOFASCORE_BASE_URL="https://api.sofascore.com/api/v1"
export SOFASCORE_RATE_LIMIT=60
export SOFASCORE_TIMEOUT=30

# Data retention settings
export SNAPSHOT_RETENTION_HOURS=48
export PREDICTION_RETENTION_HOURS=24
export LOG_RETENTION_DAYS=7

# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================

# Alert settings
export ENABLE_HIGH_CONFIDENCE_ALERTS=true
export ENABLE_IMMEDIATE_OPPORTUNITY_ALERTS=true
export ALERT_COOLDOWN_MINUTES=5

# Output formats
export GENERATE_JSON_REPORTS=true
export GENERATE_TEXT_REPORTS=true
export GENERATE_CSV_EXPORTS=true

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Concurrent processing
export MAX_CONCURRENT_MATCHES=5
export MAX_CONCURRENT_PREDICTIONS=3

# Timeouts and retries
export PREDICTION_TIMEOUT=30
export HISTORICAL_ANALYSIS_TIMEOUT=15
export MAX_RETRIES=3
export RETRY_DELAY=2

# Memory management
export MAX_SNAPSHOTS_PER_MATCH=20
export CLEANUP_INTERVAL_HOURS=6

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log levels
export LOG_LEVEL=INFO
export DEBUG_MODE=false

# Log file settings
export MAIN_LOG_FILE="$LOGS_DIR/stage7.log"
export MONITOR_LOG_FILE="$LOGS_DIR/live_monitor.log"
export PROBABILITY_LOG_FILE="$LOGS_DIR/probability_calculator.log"
export ERROR_LOG_FILE="$LOGS_DIR/errors.log"

# Log rotation
export LOG_MAX_SIZE=10485760  # 10MB
export LOG_BACKUP_COUNT=5

# =============================================================================
# DEVELOPMENT AND TESTING SETTINGS
# =============================================================================

# Test mode settings
export TEST_MODE=false
export MOCK_LIVE_DATA=false
export SIMULATE_MATCHES=false

# Demo data settings
export DEMO_MATCH_IDS="12345 12346 12347"
export DEMO_TEAMS="Arsenal:Chelsea Liverpool:ManCity Barcelona:RealMadrid"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Color codes for terminal output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export WHITE='\033[1;37m'
export NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$MAIN_LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$MAIN_LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$MAIN_LOG_FILE" "$ERROR_LOG_FILE"
}

log_debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        echo -e "${CYAN}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$MAIN_LOG_FILE"
    fi
}

# Validation functions
validate_match_id() {
    local match_id=$1
    if [[ ! "$match_id" =~ ^[0-9]+$ ]] || [ "$match_id" -lt 1000 ] || [ "$match_id" -gt 999999999 ]; then
        return 1
    fi
    return 0
}

validate_minute() {
    local minute=$1
    if [[ ! "$minute" =~ ^[0-9]+$ ]] || [ "$minute" -lt 0 ] || [ "$minute" -gt 150 ]; then
        return 1
    fi
    return 0
}

validate_probability() {
    local prob=$1
    if ! command -v bc >/dev/null 2>&1; then
        # Fallback validation without bc
        case $prob in
            0.*|1.0|1) return 0 ;;
            *) return 1 ;;
        esac
    else
        if (( $(echo "$prob >= 0 && $prob <= 1" | bc -l) )); then
            return 0
        else
            return 1
        fi
    fi
}

# File management functions
ensure_directory() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_debug "Created directory: $dir"
    fi
}

cleanup_old_files() {
    local directory=$1
    local hours=$2
    
    if [ -d "$directory" ]; then
        find "$directory" -type f -mtime +$(($hours / 24)) -delete 2>/dev/null
        log_debug "Cleaned up files older than $hours hours in $directory"
    fi
}

# Process management functions
is_process_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    kill -0 "$pid" 2>/dev/null
}

get_process_pid() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        cat "$pid_file"
    else
        echo ""
    fi
}

# JSON processing functions (without jq dependency)
extract_json_value() {
    local json_file=$1
    local key=$2
    
    if [ -f "$json_file" ]; then
        python3 -c "
import json
import sys
try:
    with open('$json_file', 'r') as f:
        data = json.load(f)
    print(data.get('$key', ''))
except:
    pass
" 2>/dev/null
    fi
}

# =============================================================================
# ENVIRONMENT VALIDATION
# =============================================================================

validate_environment() {
    log_info "🔍 Validating Stage 7 environment..."
    
    local validation_errors=0
    
    # Check Python environment
    if [ ! -f "$PYTHON_ENV/bin/activate" ]; then
        log_error "Python virtual environment not found at $PYTHON_ENV"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check required Python packages
    if [ -f "$PYTHON_ENV/bin/activate" ]; then
        source "$PYTHON_ENV/bin/activate"
        
        required_packages="pandas numpy scikit-learn"
        for package in $required_packages; do
            if ! python3 -c "import $package" 2>/dev/null; then
                log_error "Required Python package not found: $package"
                validation_errors=$((validation_errors + 1))
            fi
        done
    fi
    
    # Check ML models from Stage 6
    if [ ! -d "$MODELS_DIR/saved_models" ]; then
        log_error "Stage 6 ML models not found at $MODELS_DIR/saved_models"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check training data
    if [ ! -f "demo_training_dataset.csv" ]; then
        log_warn "Training dataset not found: demo_training_dataset.csv"
    fi
    
    # Check disk space
    available_space=$(df "$DATA_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # Less than 1GB
        log_warn "Low disk space available: ${available_space}KB"
    fi
    
    if [ $validation_errors -eq 0 ]; then
        log_info "✅ Environment validation passed"
        return 0
    else
        log_error "❌ Environment validation failed with $validation_errors errors"
        return 1
    fi
}

# =============================================================================
# INITIALIZATION
# =============================================================================

# Run validation when config is sourced
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being executed directly
    validate_environment
else
    # Script is being sourced
    log_debug "Stage 7 configuration loaded"
fi

# Export all functions for use in other scripts
export -f log_info log_warn log_error log_debug
export -f validate_match_id validate_minute validate_probability
export -f ensure_directory cleanup_old_files
export -f is_process_running get_process_pid
export -f extract_json_value validate_environment