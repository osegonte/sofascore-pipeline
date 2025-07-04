#!/bin/bash
# Stage 8 Dashboard Controller

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE8_DIR="$SCRIPT_DIR/stage8"
VENV_DIR="$SCRIPT_DIR/venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo ""
    echo -e "${BLUE}Stage 8: Dashboard & Betting Recommendations${NC}"
    echo "=============================================="
    echo ""
    echo "Usage: $0 {start|stop|status|test|setup}"
    echo ""
    echo "Commands:"
    echo "  start   - Start the dashboard server"
    echo "  stop    - Stop the dashboard server"
    echo "  status  - Show dashboard status"
    echo "  test    - Test Stage 7 integration"
    echo "  setup   - Re-run setup process"
    echo ""
}

check_stage7() {
    if [ -d "stage7/pids" ] && [ -n "$(ls -A stage7/pids 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ Stage 7 is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Stage 7 is not running${NC}"
        echo -e "   💡 Start with: ${BLUE}./stage7.sh start${NC}"
        return 1
    fi
}

start_dashboard() {
    echo -e "${BLUE}🚀 Starting Stage 8 Dashboard...${NC}"
    
    check_stage7
    echo ""
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${RED}❌ Virtual environment not found${NC}"
        exit 1
    fi
    
    # Check if port is available
    if lsof -Pi :8008 -sTCP:LISTEN -t >/dev/null; then
        echo -e "${YELLOW}⚠️  Port 8008 is already in use${NC}"
        echo "   Stop existing service or use a different port"
        exit 1
    fi
    
    echo -e "${GREEN}🌐 Dashboard URL: http://localhost:8008${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:8008/docs${NC}"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    cd "$SCRIPT_DIR"
    python3 stage8_backend.py
}

stop_dashboard() {
    echo -e "${BLUE}🛑 Stopping Stage 8 Dashboard...${NC}"
    
    # Find and kill dashboard processes
    pkill -f "stage8_backend.py" 2>/dev/null || true
    pkill -f "uvicorn.*8008" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Dashboard stopped${NC}"
}

show_status() {
    echo ""
    echo -e "${BLUE}📊 Stage 8 Dashboard Status${NC}"
    echo "============================"
    echo ""
    
    # Check if dashboard is running
    if pgrep -f "stage8_backend.py" >/dev/null; then
        echo -e "${GREEN}✅ Dashboard server: Running${NC}"
        
        if curl -s http://localhost:8008/api/system-status >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API endpoint: Accessible${NC}"
        else
            echo -e "${YELLOW}⚠️  API endpoint: Not responding${NC}"
        fi
    else
        echo -e "${RED}❌ Dashboard server: Not running${NC}"
    fi
    
    # Check Stage 7 status
    check_stage7
    
    # Check data directories
    echo ""
    echo -e "${BLUE}📁 Data Status:${NC}"
    
    if [ -f "stage7/data/realtime/live_matches.json" ]; then
        match_count=$(python3 -c "
import json
try:
    with open('stage7/data/realtime/live_matches.json', 'r') as f:
        data = json.load(f)
    print(len(data))
except:
    print(0)
" 2>/dev/null || echo "0")
        echo -e "  ${GREEN}📊 Live matches: $match_count${NC}"
    else
        echo -e "  ${YELLOW}📊 Live matches: No data${NC}"
    fi
    
    if [ -d "stage7/data/realtime/alerts" ]; then
        alert_count=$(ls stage7/data/realtime/alerts/*.json 2>/dev/null | wc -l)
        echo -e "  ${GREEN}🚨 Active alerts: $alert_count${NC}"
    else
        echo -e "  ${YELLOW}🚨 Active alerts: No data${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}💡 Quick Commands:${NC}"
    echo "   Start dashboard: ./stage8.sh start"
    echo "   View logs: tail -f stage8/logs/dashboard.log"
    echo "   Test integration: ./stage8.sh test"
    echo ""
}

test_integration() {
    echo -e "${BLUE}🧪 Testing Stage 8 Integration...${NC}"
    echo ""
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    cd "$SCRIPT_DIR"
    python3 stage8_backend.py test
}

case "${1:-}" in
    start)
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    status)
        show_status
        ;;
    test)
        test_integration
        ;;
    setup)
        echo -e "${BLUE}🔧 Re-running Stage 8 setup...${NC}"
        bash setup_stage8.sh
        ;;
    *)
        show_usage
        ;;
esac
