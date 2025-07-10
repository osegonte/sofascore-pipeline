#!/bin/bash
# run.sh - Main control script for SofaScore Data Collection

show_menu() {
    echo ""
    echo "⚽ SofaScore Live Data Pipeline - COMPLETE SYSTEM"
    echo "================================================="
    echo "1. 🔧 Setup Environment (first time only)"
    echo "2. 🎯 Start ADVANCED Complete Collection (100% fields)"
    echo "3. 🚀 Start Quality-Focused Collection (95%+ completion)"
    echo "4. 📊 Monitor Collection Status"
    echo "5. 📁 View Collected Data"
    echo "6. 🔍 Validate Data Quality"
    echo "7. 📈 Compare Collection Methods"
    echo "8. 🛑 Stop Data Collection"
    echo "9. 🧹 Project Cleanup"
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
            echo "🎯 Starting ADVANCED complete data collection..."
            ./scripts/start_advanced_collection.sh
            ;;
        3)
            echo "🚀 Starting quality-focused collection..."
            ./scripts/start_quality_focused.sh
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
            echo "📈 Comparing collection methods..."
            ./scripts/compare_methods.sh
            ;;
        8)
            echo "🛑 Stopping data collection..."
            ./scripts/stop_collection.sh
            ;;
        9)
            echo "🧹 Running project cleanup..."
            ./scripts/cleanup_project.sh
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 0-9."
            ;;
    esac
    
    if [ $choice -ne 2 ] && [ $choice -ne 3 ] && [ $choice -ne 4 ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
done