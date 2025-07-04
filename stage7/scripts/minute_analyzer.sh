#!/bin/bash
# minute_analyzer.sh - Analyzes match data minute by minute

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE7_HOME="$(dirname "$SCRIPT_DIR")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MINUTE_ANALYZER] $1"
}

log "🔄 Minute analyzer starting..."

while true; do
    # Simulate minute-by-minute analysis
    log "📊 Analyzing current minute data..."
    
    # Check for live matches
    if [ -f "$STAGE7_HOME/data/realtime/live_matches.json" ]; then
        log "📈 Processing live match data..."
    else
        log "📭 No live matches to analyze"
    fi
    
    # Wait 60 seconds (1 minute)
    sleep 60
done
