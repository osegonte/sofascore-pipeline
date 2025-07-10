#!/bin/bash
# run.sh - Streamlined main control script

show_menu() {
    echo ""
    echo "⚽ SofaScore Data Collection Pipeline - STREAMLINED"
    echo "=================================================="
    echo "1. 🔧 Setup Environment"
    echo "2. 🚀 Start Data Collection"
    echo "3. 📊 Monitor Collection Status"
    echo "4. 📁 View Collected Data"
    echo "5. 🔍 Validate Data Quality"
    echo "6. 📈 Performance Analysis"
    echo "7. 🛑 Stop Data Collection"
    echo "8. 🧹 Database Management"
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
            echo "🚀 Starting data collection..."
            ./scripts/start_collection.sh
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
            echo "📈 Analyzing performance..."
            ./scripts/compare_performance.sh
            ;;
        7)
            echo "🛑 Stopping data collection..."
            ./scripts/stop_collection.sh
            ;;
        8)
            echo "🧹 Opening database management..."
            python database/db_manager.py status
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 0-8."
            ;;
    esac
    
    if [ $choice -ne 2 ] && [ $choice -ne 3 ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
done
