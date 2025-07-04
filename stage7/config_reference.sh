#!/bin/bash
# Configuration reference for Stage 7 - FIXED PATHS

export STAGE7_HOME="${STAGE7_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
export PYTHON_ENV="$STAGE7_HOME/../venv"
export DATA_DIR="$STAGE7_HOME/data"
export LOGS_DIR="$STAGE7_HOME/logs"
export MODELS_DIR="$STAGE7_HOME/../data/models"
export REALTIME_DIR="$STAGE7_HOME/data/realtime"

# Key minutes for enhanced monitoring
export KEY_MINUTES="59 60 69 70 79 80"

# Ensemble weights
export ML_WEIGHT=0.7
export HISTORICAL_WEIGHT=0.3

# Confidence thresholds
export HIGH_CONFIDENCE_THRESHOLD=0.6
export HIGH_PROB_THRESHOLD=0.7
export LOW_PROB_THRESHOLD=0.3

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
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

# Export functions
export -f log_info log_warn log_error validate_match_id validate_minute
