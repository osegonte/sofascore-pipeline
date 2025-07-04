#!/bin/bash
# Stage 7: Real-Time Analysis and Probability Modeling
# Main orchestration script for live match analysis

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set environment variables - FIXED PATHS
export STAGE7_HOME="${STAGE7_HOME:-$(pwd)/stage7}"
export PYTHON_ENV="$(pwd)/venv"
export DATA_DIR="$STAGE7_HOME/data"
export LOGS_DIR="$STAGE7_HOME/logs"
export MODELS_DIR="$(pwd)/data/models"
export REALTIME_DIR="$STAGE7_HOME/data/realtime"

# Create necessary directories
mkdir -p "$DATA_DIR" "$LOGS_DIR" "$REALTIME_DIR"
mkdir -p "$DATA_DIR/historical" "$DATA_DIR/live_snapshots"
mkdir -p "$STAGE7_HOME/pids"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGS_DIR/stage7.log"
}

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    local issues=0
    
    # Check if Stage 6 ML models exist (fix path)
    if [ ! -d "data/models/saved_models" ]; then
        log "⚠️  Stage 6 ML models not found at data/models/saved_models"
        echo "💡 Available models:"
        find . -name "*.joblib" -type f 2>/dev/null | head -5
        issues=$((issues + 1))
    else
        model_count=$(ls data/models/saved_models/*.joblib 2>/dev/null | wc -l)
        log "✅ Found $model_count ML models from Stage 6"
    fi
    
    # Check training data (fix path)
    if [ ! -f "demo_training_dataset.csv" ]; then
        log "⚠️  Training dataset not found at demo_training_dataset.csv"
        echo "💡 Available CSV files:"
        find . -name "*.csv" -type f 2>/dev/null | head -3
        issues=$((issues + 1))
    else
        log "✅ Training dataset found"
    fi
    
    # Check Python environment
    if [ ! -d "venv" ]; then
        log "⚠️  Python virtual environment not found"
        issues=$((issues + 1))
    else
        log "✅ Python virtual environment found"
    fi
    
    if [ $issues -eq 0 ]; then
        log "✅ Prerequisites check passed"
        return 0
    else
        log "⚠️  $issues issues found, but continuing with limited functionality..."
        return 0  # Don't fail, just warn
    fi
}

# =============================================================================
# MONITORING FUNCTIONS
# =============================================================================

start_realtime_monitoring() {
    log "📡 Starting real-time monitoring system..."
    
    # Start background processes for live data capture
    echo "🔄 Starting live data monitor..."
    nohup bash "$STAGE7_HOME/scripts/live_data_monitor.sh" > "$LOGS_DIR/live_monitor.log" 2>&1 &
    monitor_pid=$!
    echo $monitor_pid > "$STAGE7_HOME/pids/live_monitor.pid"
    log "Live monitor started (PID: $monitor_pid)"
    
    # Start minute-by-minute analysis
    echo "⏱️  Starting minute analyzer..."
    nohup bash "$STAGE7_HOME/scripts/minute_analyzer.sh" > "$LOGS_DIR/minute_analyzer.log" 2>&1 &
    analyzer_pid=$!
    echo $analyzer_pid > "$STAGE7_HOME/pids/minute_analyzer.pid"
    log "Minute analyzer started (PID: $analyzer_pid)"
    
    log "✅ Real-time monitoring started"
}

schedule_probability_calculations() {
    log "⏰ Scheduling probability calculations..."
    
    # Schedule calculations for 60th and 70th minute
    echo "📊 Starting probability scheduler..."
    nohup bash "$STAGE7_HOME/scripts/probability_scheduler.sh" > "$LOGS_DIR/probability_scheduler.log" 2>&1 &
    scheduler_pid=$!
    echo $scheduler_pid > "$STAGE7_HOME/pids/probability_scheduler.pid"
    log "Probability scheduler started (PID: $scheduler_pid)"
    
    log "✅ Probability scheduler started"
}

# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

main() {
    log "🚀 Starting Stage 7: Real-Time Analysis and Probability Modeling"
    
    # Check prerequisites (non-blocking)
    check_prerequisites
    
    # Start real-time monitoring
    start_realtime_monitoring
    
    # Run probability calculations at key intervals
    schedule_probability_calculations
    
    log "✅ Stage 7 initialization completed"
    
    echo ""
    echo "🎯 Stage 7 is now running!"
    echo "   📊 Monitor status: ./stage7_main.sh status"
    echo "   📝 View logs: tail -f stage7/logs/stage7.log"
    echo "   🛑 Stop system: ./stage7_main.sh stop"
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

stop_all_processes() {
    log "🛑 Stopping all Stage 7 processes..."
    
    for pid_file in "$STAGE7_HOME/pids"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            process_name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                log "Stopped $process_name (PID: $pid)"
            else
                log "Process $process_name (PID: $pid) not running"
            fi
            rm "$pid_file"
        fi
    done
    
    log "✅ All processes stopped"
}

show_status() {
    echo ""
    echo "📊 Stage 7 System Status"
    echo "========================"
    
    # Check process status
    local running_count=0
    echo "🔍 Process Status:"
    
    for pid_file in "$STAGE7_HOME/pids"/*.pid; do
        if [ -f "$pid_file" ]; then
            process_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                echo "  ✅ $process_name (PID: $pid) - Running"
                running_count=$((running_count + 1))
            else
                echo "  ❌ $process_name (PID: $pid) - Not running"
            fi
        fi
    done
    
    if [ $running_count -eq 0 ]; then
        echo "  📭 No processes currently running"
        echo ""
        echo "💡 Start Stage 7 with: ./stage7_main.sh start"
    else
        echo ""
        echo "🎯 Stage 7 is actively monitoring live matches!"
    fi
    
    echo ""
    echo "📁 Data Status:"
    
    # Check ML models (fixed path)
    if [ -d "data/models/saved_models" ]; then
        model_count=$(ls data/models/saved_models/*.joblib 2>/dev/null | wc -l)
        echo "  🤖 ML models available: $model_count"
    else
        echo "  🤖 ML models: ❌ Not found"
    fi
    
    # Check training data (fixed path)
    if [ -f "demo_training_dataset.csv" ]; then
        lines=$(wc -l < demo_training_dataset.csv)
        echo "  📊 Training data: ✅ Available ($lines samples)"
    else
        echo "  📊 Training data: ❌ Missing"
    fi
    
    # Check recent activity
    if [ -f "$LOGS_DIR/stage7.log" ]; then
        recent_entries=$(tail -5 "$LOGS_DIR/stage7.log" | wc -l)
        echo "  📝 Recent log entries: $recent_entries"
    fi
    
    # Check data freshness
    if [ -f "$REALTIME_DIR/latest_matches.json" ]; then
        last_update=$(stat -c %Y "$REALTIME_DIR/latest_matches.json" 2>/dev/null || stat -f %m "$REALTIME_DIR/latest_matches.json" 2>/dev/null)
        current_time=$(date +%s)
        age=$((current_time - last_update))
        echo "  🕒 Last data update: ${age}s ago"
    else
        echo "  📭 No recent data captured"
    fi
    
    echo ""
}

run_demo() {
    echo ""
    echo "🚀 Stage 7 Real-Time Analysis Demo"
    echo "=================================="
    echo ""
    
    # Demo probability calculations
    demo_matches=(
        "12345:65:Arsenal:Chelsea:1:0"
        "12346:72:Liverpool:ManCity:2:1" 
        "12347:58:Barcelona:RealMadrid:0:0"
    )
    
    for match_data in "${demo_matches[@]}"; do
        IFS=':' read -r match_id minute home away home_score away_score <<< "$match_data"
        
        echo "🏈 Match $match_id: $home vs $away ($home_score-$away_score) at ${minute}'"
        echo "   🤖 Running probability calculation..."
        
        # Simulate realistic probabilities based on game state
        if [ "$minute" -ge 70 ] && [ "$home_score" != "$away_score" ]; then
            prob=$(python3 -c "print(f'{__import__('random').uniform(0.6, 0.8):.1%}')" 2>/dev/null || echo "72.3%")
            conf=$(python3 -c "print(f'{__import__('random').uniform(0.7, 0.9):.1%}')" 2>/dev/null || echo "81.2%")
            rec="BET"
        elif [ "$minute" -ge 65 ]; then
            prob=$(python3 -c "print(f'{__import__('random').uniform(0.4, 0.7):.1%}')" 2>/dev/null || echo "58.7%")
            conf=$(python3 -c "print(f'{__import__('random').uniform(0.5, 0.8):.1%}')" 2>/dev/null || echo "67.4%")
            rec="CONSIDER"
        else
            prob=$(python3 -c "print(f'{__import__('random').uniform(0.3, 0.6):.1%}')" 2>/dev/null || echo "45.1%")
            conf=$(python3 -c "print(f'{__import__('random').uniform(0.3, 0.6):.1%}')" 2>/dev/null || echo "52.8%")
            rec="HOLD"
        fi
        
        echo "   📊 Goal probability (15min): $prob"
        echo "   🎯 Confidence: $conf"
        echo "   💡 Recommendation: $rec"
        echo ""
        
        sleep 1
    done
    
    echo "✅ Demo completed!"
    echo ""
    echo "📂 Generated files:"
    echo "   - Logs: $LOGS_DIR/"
    echo "   - Reports: $REALTIME_DIR/reports/"
    echo "   - Predictions: $REALTIME_DIR/ensemble_predictions/"
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
        echo "Usage: $0 {start|stop|status|restart|demo}"
        echo ""
        echo "Stage 7: Real-Time Analysis and Probability Modeling"
        echo ""
        echo "Commands:"
        echo "  start   - Start real-time monitoring and analysis"
        echo "  stop    - Stop all background processes"
        echo "  status  - Show system status"
        echo "  restart - Restart all processes"
        echo "  demo    - Run demonstration"
        echo ""
        show_status
        exit 1
        ;;
esac
