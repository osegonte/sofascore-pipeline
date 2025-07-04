#!/bin/bash
# scripts/probability_scheduler.sh
# Scheduler for triggering probability calculations at optimal times

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE7_HOME="$(dirname "$SCRIPT_DIR")"
source "$STAGE7_HOME/config/stage7_config.sh"

# Scheduler settings
SCHEDULE_CHECK_INTERVAL=15  # Check every 15 seconds
CALCULATION_COOLDOWN=60     # Minimum seconds between calculations for same match

# =============================================================================
# LOGGING AND UTILITIES
# =============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SCHEDULER] $1" | tee -a "$LOGS_DIR/probability_scheduler.log"
}

# =============================================================================
# SCHEDULING LOGIC
# =============================================================================

is_key_minute() {
    local minute=$1
    
    # Check if this is one of our target minutes
    for key_min in $KEY_MINUTES; do
        if [ "$minute" -eq "$key_min" ]; then
            return 0
        fi
    done
    
    return 1
}

should_calculate_now() {
    local match_id=$1
    local minute=$2
    
    # Check if we've calculated recently for this match
    local last_calc_file="$REALTIME_DIR/last_calculations/match_${match_id}.txt"
    
    if [ -f "$last_calc_file" ]; then
        local last_calc_time=$(cat "$last_calc_file")
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_calc_time))
        
        if [ $time_diff -lt $CALCULATION_COOLDOWN ]; then
            log_debug "Calculation cooldown active for match $match_id (${time_diff}s < ${CALCULATION_COOLDOWN}s)"
            return 1
        fi
    fi
    
    # Check if this is a key minute
    if is_key_minute "$minute"; then
        return 0
    fi
    
    # Check if this is late in the game (75+ minutes) - calculate more frequently
    if [ "$minute" -ge 75 ]; then
        return 0
    fi
    
    return 1
}

record_calculation() {
    local match_id=$1
    
    local last_calc_dir="$REALTIME_DIR/last_calculations"
    ensure_directory "$last_calc_dir"
    
    echo "$(date +%s)" > "$last_calc_dir/match_${match_id}.txt"
}

# =============================================================================
# MATCH MONITORING
# =============================================================================

get_active_matches() {
    log_debug "Getting active matches for probability scheduling"
    
    # Check for live matches data
    if [ -f "$REALTIME_DIR/live_matches.json" ]; then
        python3 -c "
import json
import sys

try:
    with open('$REALTIME_DIR/live_matches.json', 'r') as f:
        matches = json.load(f)
    
    active_matches = []
    for match in matches:
        minute = match.get('minute', 0)
        
        # Only consider matches in our target range
        if $MIN_MINUTE_THRESHOLD <= minute <= $MAX_MINUTE_THRESHOLD:
            active_matches.append(match)
    
    for match in active_matches:
        print(f\"{match['match_id']}:{match['minute']}:{match.get('home_team', 'Home')}:{match.get('away_team', 'Away')}:{match.get('home_score', 0)}:{match.get('away_score', 0)}\")
        
except Exception as e:
    print(f'ERROR:Could not read live matches: {e}', file=sys.stderr)
"
    else
        log_debug "No live matches file found"
    fi
}

# =============================================================================
# CALCULATION TRIGGERS
# =============================================================================

trigger_calculation() {
    local match_id=$1
    local minute=$2
    local home_team=$3
    local away_team=$4
    local home_score=$5
    local away_score=$6
    
    log "🎯 Triggering probability calculation for match $match_id at minute $minute"
    
    # Create background job for calculation
    {
        # Run probability calculation
        bash "$STAGE7_HOME/scripts/calculate_probabilities.sh" \
            "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score"
        
        # Record that we calculated
        record_calculation "$match_id"
        
        # Check if this generated high-confidence recommendations
        check_for_alerts "$match_id" "$minute"
        
    } &
    
    local calc_pid=$!
    log "Started calculation job (PID: $calc_pid) for match $match_id"
}

check_for_alerts() {
    local match_id=$1
    local minute=$2
    
    local ensemble_file="$REALTIME_DIR/ensemble_predictions/match_${match_id}_minute_${minute}.json"
    
    if [ -f "$ensemble_file" ]; then
        python3 -c "
import json
import sys

def check_alert_conditions(data):
    '''Check if this prediction warrants an alert'''
    
    try:
        confidence = data.get('confidence_score', 0)
        recommendations = data.get('betting_recommendations', {})
        action = recommendations.get('action', 'HOLD')
        confidence_level = recommendations.get('confidence_level', 'LOW')
        
        # High confidence betting opportunity
        if confidence >= 0.6 and action == 'BET':
            return True, f'HIGH CONFIDENCE BETTING OPPORTUNITY'
        
        # Immediate opportunity (next minute)
        recommended_bets = recommendations.get('recommended_bets', [])
        for bet in recommended_bets:
            if bet.get('urgency') == 'IMMEDIATE':
                return True, f'IMMEDIATE BETTING OPPORTUNITY'
        
        # High probability events
        probs = data.get('ensemble_probabilities', {})
        if probs.get('goal_next_15min', 0) >= 0.8:
            return True, f'HIGH PROBABILITY GOAL EXPECTED'
        
        return False, ''
        
    except Exception as e:
        return False, f'Error checking alerts: {e}'

try:
    with open('$ensemble_file', 'r') as f:
        data = json.load(f)
    
    should_alert, message = check_alert_conditions(data)
    
    if should_alert:
        match_info = data.get('match_info', {})
        print(f'ALERT:{data[\"match_id\"]}:{data[\"minute\"]}:{message}:{match_info.get(\"home_team\", \"\")}:{match_info.get(\"away_team\", \"\")}')
    else:
        print('NO_ALERT')
        
except Exception as e:
    print(f'ERROR:Could not check alerts: {e}')
" | while IFS=':' read -r type match_id minute message home_team away_team; do
            case $type in
                ALERT)
                    log "🚨 ALERT: Match $match_id at minute $minute - $message"
                    generate_alert "$match_id" "$minute" "$message" "$home_team" "$away_team"
                    ;;
                NO_ALERT)
                    log_debug "No alerts for match $match_id at minute $minute"
                    ;;
                ERROR)
                    log_error "Alert check error: $match_id"
                    ;;
            esac
        done
    fi
}

generate_alert() {
    local match_id=$1
    local minute=$2
    local message=$3
    local home_team=$4
    local away_team=$5
    
    # Create alert file
    local alert_dir="$REALTIME_DIR/alerts"
    ensure_directory "$alert_dir"
    
    local alert_file="$alert_dir/alert_$(date +%Y%m%d_%H%M%S)_match_${match_id}.json"
    
    cat > "$alert_file" << EOF
{
    "alert_id": "$(date +%Y%m%d_%H%M%S)_${match_id}",
    "match_id": $match_id,
    "minute": $minute,
    "message": "$message",
    "match_info": {
        "home_team": "$home_team",
        "away_team": "$away_team"
    },
    "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "alert_type": "betting_opportunity",
    "priority": "high",
    "processed": false
}
EOF
    
    # Log the alert
    log "🚨 ALERT GENERATED: $message for $home_team vs $away_team (Match $match_id, Minute $minute)"
    
    # If notifications are enabled, trigger them
    if [ "$ENABLE_HIGH_CONFIDENCE_ALERTS" = "true" ]; then
        send_notification "$match_id" "$minute" "$message" "$home_team" "$away_team"
    fi
}

send_notification() {
    local match_id=$1
    local minute=$2
    local message=$3
    local home_team=$4
    local away_team=$5
    
    # Simple notification system (can be extended)
    local notification_text="⚽ BETTING ALERT: $message
Match: $home_team vs $away_team
Minute: $minute
Time: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Write to notification file
    echo "$notification_text" >> "$LOGS_DIR/notifications.log"
    
    # Display on terminal if running interactively
    if [ -t 1 ]; then
        echo -e "\n${RED}🚨 BETTING ALERT 🚨${NC}"
        echo -e "${WHITE}$notification_text${NC}\n"
    fi
    
    log "📱 Notification sent for match $match_id"
}

# =============================================================================
# SCHEDULED CALCULATION TYPES
# =============================================================================

schedule_regular_calculations() {
    log_debug "Running scheduled regular calculations..."
    
    get_active_matches | while IFS=':' read -r match_id minute home_team away_team home_score away_score; do
        if [ -n "$match_id" ] && validate_match_id "$match_id" && validate_minute "$minute"; then
            if should_calculate_now "$match_id" "$minute"; then
                log "📅 Scheduled calculation for match $match_id at minute $minute"
                trigger_calculation "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score"
            else
                log_debug "Skipping calculation for match $match_id (not needed yet)"
            fi
        fi
    done
}

schedule_key_minute_calculations() {
    log_debug "Checking for key minute calculations..."
    
    get_active_matches | while IFS=':' read -r match_id minute home_team away_team home_score away_score; do
        if [ -n "$match_id" ] && validate_match_id "$match_id" && validate_minute "$minute"; then
            if is_key_minute "$minute"; then
                # Force calculation regardless of cooldown for key minutes
                log "🎯 KEY MINUTE: Forcing calculation for match $match_id at minute $minute"
                trigger_calculation "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score"
            fi
        fi
    done
}

schedule_late_game_calculations() {
    log_debug "Checking for late game calculations..."
    
    get_active_matches | while IFS=':' read -r match_id minute home_team away_team home_score away_score; do
        if [ -n "$match_id" ] && validate_match_id "$match_id" && validate_minute "$minute"; then
            # Late game: 75+ minutes
            if [ "$minute" -ge 75 ]; then
                # More frequent calculations in late game
                local short_cooldown=30  # 30 seconds cooldown for late game
                
                local last_calc_file="$REALTIME_DIR/last_calculations/match_${match_id}.txt"
                local should_calc=true
                
                if [ -f "$last_calc_file" ]; then
                    local last_calc_time=$(cat "$last_calc_file")
                    local current_time=$(date +%s)
                    local time_diff=$((current_time - last_calc_time))
                    
                    if [ $time_diff -lt $short_cooldown ]; then
                        should_calc=false
                    fi
                fi
                
                if [ "$should_calc" = "true" ]; then
                    log "⏰ LATE GAME: Enhanced calculation for match $match_id at minute $minute"
                    trigger_calculation "$match_id" "$minute" "$home_team" "$away_team" "$home_score" "$away_score"
                fi
            fi
        fi
    done
}

# =============================================================================
# CLEANUP AND MAINTENANCE
# =============================================================================

cleanup_old_calculations() {
    log_debug "Cleaning up old calculation records..."
    
    # Clean up old calculation timestamps
    local last_calc_dir="$REALTIME_DIR/last_calculations"
    if [ -d "$last_calc_dir" ]; then
        find "$last_calc_dir" -type f -mtime +1 -delete 2>/dev/null
    fi
    
    # Clean up old predictions
    cleanup_old_files "$REALTIME_DIR/ml_predictions" 24
    cleanup_old_files "$REALTIME_DIR/historical_predictions" 24
    cleanup_old_files "$REALTIME_DIR/ensemble_predictions" 48
    
    # Clean up old snapshots
    cleanup_old_files "$REALTIME_DIR/snapshots" 48
    
    # Archive old alerts
    local alert_dir="$REALTIME_DIR/alerts"
    if [ -d "$alert_dir" ]; then
        # Move alerts older than 24 hours to archive
        local archive_dir="$alert_dir/archive"
        ensure_directory "$archive_dir"
        
        find "$alert_dir" -maxdepth 1 -name "alert_*.json" -mtime +1 -exec mv {} "$archive_dir/" \; 2>/dev/null
        
        # Delete archived alerts older than 7 days
        find "$archive_dir" -type f -mtime +7 -delete 2>/dev/null
    fi
    
    log_debug "Cleanup completed"
}

# =============================================================================
# HEALTH MONITORING
# =============================================================================

check_system_health() {
    log_debug "Checking system health..."
    
    local health_issues=0
    
    # Check if live data monitor is running
    local monitor_pid_file="$STAGE7_HOME/pids/live_monitor.pid"
    local monitor_pid=$(get_process_pid "$monitor_pid_file")
    
    if [ -n "$monitor_pid" ] && is_process_running "$monitor_pid"; then
        log_debug "Live monitor running (PID: $monitor_pid)"
    else
        log_warn "Live monitor not running!"
        health_issues=$((health_issues + 1))
    fi
    
    # Check data freshness
    if [ -f "$REALTIME_DIR/live_matches.json" ]; then
        local last_update=$(stat -c %Y "$REALTIME_DIR/live_matches.json" 2>/dev/null || stat -f %m "$REALTIME_DIR/live_matches.json" 2>/dev/null)
        local current_time=$(date +%s)
        local age=$((current_time - last_update))
        
        if [ $age -gt 300 ]; then  # 5 minutes
            log_warn "Live data is stale (${age}s old)"
            health_issues=$((health_issues + 1))
        fi
    else
        log_warn "No live matches data found"
        health_issues=$((health_issues + 1))
    fi
    
    # Check disk space
    local available_space=$(df "$DATA_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 524288 ]; then  # Less than 500MB
        log_warn "Low disk space: ${available_space}KB available"
        health_issues=$((health_issues + 1))
    fi
    
    # Check calculation queue
    local active_calculations=$(pgrep -f "calculate_probabilities.sh" | wc -l)
    if [ "$active_calculations" -gt 10 ]; then
        log_warn "High number of active calculations: $active_calculations"
        health_issues=$((health_issues + 1))
    fi
    
    if [ $health_issues -eq 0 ]; then
        log_debug "System health check passed"
    else
        log_warn "System health check found $health_issues issues"
    fi
    
    return $health_issues
}

# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

log_performance_metrics() {
    local metrics_file="$REALTIME_DIR/performance_metrics.json"
    
    # Count active processes
    local active_calculations=$(pgrep -f "calculate_probabilities.sh" | wc -l)
    local active_monitors=$(pgrep -f "live_data_monitor.sh" | wc -l)
    
    # Count recent predictions
    local recent_predictions=0
    if [ -d "$REALTIME_DIR/ensemble_predictions" ]; then
        recent_predictions=$(find "$REALTIME_DIR/ensemble_predictions" -name "*.json" -mmin -60 | wc -l)
    fi
    
    # Count alerts
    local recent_alerts=0
    if [ -d "$REALTIME_DIR/alerts" ]; then
        recent_alerts=$(find "$REALTIME_DIR/alerts" -name "alert_*.json" -mmin -60 | wc -l)
    fi
    
    # System load
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    cat > "$metrics_file" << EOF
{
    "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "active_processes": {
        "calculations": $active_calculations,
        "monitors": $active_monitors
    },
    "recent_activity": {
        "predictions_last_hour": $recent_predictions,
        "alerts_last_hour": $recent_alerts
    },
    "system_metrics": {
        "load_average": "$load_avg",
        "disk_available_kb": $(df "$DATA_DIR" | awk 'NR==2 {print $4}')
    }
}
EOF
    
    log_debug "Performance metrics logged"
}

# =============================================================================
# MAIN SCHEDULER LOOP
# =============================================================================

main_scheduler_loop() {
    log "🔄 Starting probability scheduler loop (check interval: ${SCHEDULE_CHECK_INTERVAL}s)"
    
    local loop_count=0
    local last_cleanup=0
    local last_health_check=0
    local last_metrics=0
    
    while true; do
        loop_count=$((loop_count + 1))
        current_time=$(date +%s)
        
        # Regular scheduling checks
        schedule_key_minute_calculations
        schedule_late_game_calculations
        
        # Every 4th iteration (1 minute), do regular calculations
        if [ $((loop_count % 4)) -eq 0 ]; then
            schedule_regular_calculations
        fi
        
        # Cleanup every 24 iterations (6 minutes)
        if [ $((loop_count % 24)) -eq 0 ] || [ $((current_time - last_cleanup)) -gt 360 ]; then
            cleanup_old_calculations
            last_cleanup=$current_time
        fi
        
        # Health check every 40 iterations (10 minutes)
        if [ $((loop_count % 40)) -eq 0 ] || [ $((current_time - last_health_check)) -gt 600 ]; then
            check_system_health
            last_health_check=$current_time
        fi
        
        # Performance metrics every 20 iterations (5 minutes)
        if [ $((loop_count % 20)) -eq 0 ] || [ $((current_time - last_metrics)) -gt 300 ]; then
            log_performance_metrics
            last_metrics=$current_time
        fi
        
        # Status update every 120 iterations (30 minutes)
        if [ $((loop_count % 120)) -eq 0 ]; then
            log "📊 Scheduler status: $loop_count iterations completed"
        fi
        
        # Sleep before next check
        sleep $SCHEDULE_CHECK_INTERVAL
    done
}

# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

cleanup_scheduler() {
    log "🧹 Cleaning up probability scheduler..."
    
    # Kill any remaining calculation jobs
    pkill -f "calculate_probabilities.sh" 2>/dev/null || true
    
    # Final performance metrics
    log_performance_metrics
    
    log "✅ Probability scheduler cleanup completed"
}

# Trap signals for clean shutdown
trap cleanup_scheduler EXIT INT TERM

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Ensure required directories exist
ensure_directory "$REALTIME_DIR/last_calculations"
ensure_directory "$REALTIME_DIR/alerts"

# Validate environment
if ! validate_environment; then
    log_error "Environment validation failed. Cannot start scheduler."
    exit 1
fi

# Start main loop
log "🚀 Probability Scheduler starting..."
log "   Schedule check interval: ${SCHEDULE_CHECK_INTERVAL}s"
log "   Key minutes: $KEY_MINUTES"
log "   Calculation cooldown: ${CALCULATION_COOLDOWN}s"

main_scheduler_loop