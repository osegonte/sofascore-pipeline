#!/bin/bash
# run_quality_focused.sh - Enhanced control script with quality focus

show_menu() {
    echo ""
    echo "⚽ SofaScore Live Data Pipeline - QUALITY FOCUSED"
    echo "=================================================="
    echo "1. 🔧 Setup Environment (first time only)"
    echo "2. 🚀 Start Original Scraper"
    echo "3. 🚀 Start Enhanced Scraper"
    echo "4. 🎯 Start QUALITY-FOCUSED Scraper (NEW!)"
    echo "5. 📊 Monitor Collection Status"
    echo "6. 📁 View Collected Data"
    echo "7. 🔍 Validate Data Quality"
    echo "8. 📈 Compare Scraper Performance"
    echo "9. 🛑 Stop Data Collection"
    echo "0. 🚪 Exit"
    echo ""
}

while true; do
    show_menu
    read -p "Select option (0-9): " choice
    
    case $choice in
        1)
            echo "🔧 Running environment setup..."
            ./scripts/setup_environment.sh
            ;;
        2)
            echo "🚀 Starting original data collection..."
            ./scripts/start_live_scraper.sh
            ;;
        3)
            echo "🚀 Starting enhanced data collection..."
            ./scripts/start_enhanced_scraper.sh
            ;;
        4)
            echo "🎯 Starting QUALITY-FOCUSED data collection..."
            ./start_quality_focused.sh
            ;;
        5)
            echo "📊 Opening monitoring dashboard..."
            ./scripts/monitor_scraper.sh
            ;;
        6)
            echo "📁 Opening data viewer..."
            ./scripts/view_data.sh
            ;;
        7)
            echo "🔍 Running data validation..."
            ./scripts/validate_data.sh
            ;;
        8)
            echo "📈 Comparing scraper performance..."
            ./scripts/compare_scrapers.sh
            ;;
        9)
            echo "🛑 Stopping data collection..."
            ./scripts/stop_live_scraper.sh
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 0-9."
            ;;
    esac
    
    if [ $choice -ne 4 ] && [ $choice -ne 5 ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
done
