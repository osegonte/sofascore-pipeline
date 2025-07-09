#!/bin/bash
# run_enhanced.sh - Main control script with enhanced scraper option

show_menu() {
    echo ""
    echo "⚽ SofaScore Live Data Pipeline - ENHANCED"
    echo "=========================================="
    echo "1. 🔧 Setup Environment (first time only)"
    echo "2. 🚀 Start Data Collection (Original)"
    echo "3. 🚀 Start ENHANCED Data Collection (NEW!)"
    echo "4. 📊 Monitor Collection Status"
    echo "5. 📁 View Collected Data"
    echo "6. 🔍 Validate Data Quality"
    echo "7. 🛑 Stop Data Collection"
    echo "8. 🧹 Project Cleanup"
    echo "0. 🚪 Exit"
    echo ""
}

while true; do
    show_menu
    read -p "Select option (0-8): " choice
    
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
            echo "🚀 Starting ENHANCED data collection..."
            ./scripts/start_enhanced_scraper.sh
            ;;
        4)
            echo "📊 Opening monitoring dashboard..."
            ./scripts/monitor_scraper.sh
            ;;
        5)
            echo "📁 Opening data viewer..."
            ./scripts/view_data.sh
            ;;
        6)
            echo "🔍 Running data validation..."
            ./scripts/validate_data.sh
            ;;
        7)
            echo "🛑 Stopping data collection..."
            ./scripts/stop_live_scraper.sh
            ;;
        8)
            echo "🧹 Running project cleanup..."
            ./scripts/cleanup_project.sh
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 0-8."
            ;;
    esac
    
    if [ $choice -ne 2 ] && [ $choice -ne 3 ] && [ $choice -ne 4 ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
done
