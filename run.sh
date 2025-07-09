#!/bin/bash
# run.sh - Main control script for SofaScore Pipeline

show_menu() {
    echo ""
    echo "⚽ SofaScore Live Data Pipeline"
    echo "==============================="
    echo "1. 🔧 Setup Environment (first time only)"
    echo "2. 🚀 Start Data Collection"
    echo "3. 📊 Monitor Collection Status"
    echo "4. 📁 View Collected Data"
    echo "5. 🔍 Validate Data Quality"
    echo "6. 🛑 Stop Data Collection"
    echo "7. 🧹 Project Cleanup"
    echo "0. 🚪 Exit"
    echo ""
}

while true; do
    show_menu
    read -p "Select option (0-7): " choice
    
    case $choice in
        1)
            echo "🔧 Running environment setup..."
            ./scripts/setup_environment.sh
            ;;
        2)
            echo "🚀 Starting data collection..."
            ./scripts/start_live_scraper.sh
            ;;
        3)
            echo "📊 Opening monitoring dashboard..."
            ./scripts/monitor_scraper.sh
            ;;
        4)
            echo "📁 Opening data viewer..."
            ./scripts/view_data.sh
            ;;
        5)
            echo "🔍 Running data validation..."
            ./scripts/validate_data.sh
            ;;
        6)
            echo "🛑 Stopping data collection..."
            ./scripts/stop_live_scraper.sh
            ;;
        7)
            echo "🧹 Running project cleanup..."
            ./scripts/cleanup_project.sh
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 0-7."
            ;;
    esac
    
    if [ $choice -ne 2 ] && [ $choice -ne 3 ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
done
