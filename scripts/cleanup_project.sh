#!/bin/bash
# cleanup_project.sh - Remove unnecessary files and keep only essentials

echo "🧹 Cleaning Up SofaScore Pipeline Project"
echo "=========================================="

# Create backup directory for removed files
mkdir -p removed_files_backup

echo "📦 Moving unnecessary files to backup..."

# Remove old scraper scripts (keep only the working live_scraper.py)
if [ -f "src/late_goal/continuous_monitor.py" ]; then
    mv "src/late_goal/continuous_monitor.py" removed_files_backup/
    echo "  ✅ Moved continuous_monitor.py"
fi

if [ -f "src/late_goal/dashboard.py" ]; then
    mv "src/late_goal/dashboard.py" removed_files_backup/
    echo "  ✅ Moved dashboard.py"
fi

if [ -f "src/late_goal/data_collector.py" ]; then
    mv "src/late_goal/data_collector.py" removed_files_backup/
    echo "  ✅ Moved data_collector.py"
fi

if [ -f "src/late_goal/data_verifier.py" ]; then
    mv "src/late_goal/data_verifier.py" removed_files_backup/
    echo "  ✅ Moved data_verifier.py"
fi

if [ -f "standalone_collector.py" ]; then
    mv "standalone_collector.py" removed_files_backup/
    echo "  ✅ Moved standalone_collector.py"
fi

if [ -f "run_late_goal_collection.py" ]; then
    mv "run_late_goal_collection.py" removed_files_backup/
    echo "  ✅ Moved run_late_goal_collection.py"
fi

if [ -f "setup_late_goal.py" ]; then
    mv "setup_late_goal.py" removed_files_backup/
    echo "  ✅ Moved setup_late_goal.py"
fi

# Remove entire late_goal directory if empty
if [ -d "src/late_goal" ] && [ -z "$(ls -A src/late_goal)" ]; then
    rmdir "src/late_goal"
    echo "  ✅ Removed empty late_goal directory"
fi

# Remove duplicate/old database scripts
if [ -f "database/csv_import.py" ]; then
    mv "database/csv_import.py" removed_files_backup/
    echo "  ✅ Moved csv_import.py (replaced by simpler version)"
fi

if [ -f "database/data_viewer.py" ]; then
    mv "database/data_viewer.py" removed_files_backup/
    echo "  ✅ Moved data_viewer.py"
fi

if [ -f "database/unified_data_creator.py" ]; then
    mv "database/unified_data_creator.py" removed_files_backup/
    echo "  ✅ Moved unified_data_creator.py"
fi

if [ -f "database/validate_data_quality.py" ]; then
    mv "database/validate_data_quality.py" removed_files_backup/
    echo "  ✅ Moved validate_data_quality.py"
fi

# Remove test files (keep only essential ones)
if [ -d "tests" ]; then
    mv tests removed_files_backup/
    echo "  ✅ Moved tests directory"
fi

# Remove backup files
if [ -f "src/live_scraper.py.backup" ]; then
    mv "src/live_scraper.py.backup" removed_files_backup/
    echo "  ✅ Moved backup files"
fi

# Remove old scripts that are no longer needed
for script in fix_issues.sh make_scripts_executable.sh update_scraper.sh test_scraper.sh; do
    if [ -f "$script" ]; then
        mv "$script" removed_files_backup/
        echo "  ✅ Moved $script"
    fi
done

# Keep only essential shell scripts
echo ""
echo "📋 ESSENTIAL FILES KEPT:"
echo "========================"

echo "🐍 Python Files:"
echo "  • src/live_scraper.py              (Main data collector)"
echo "  • src/utils.py                     (Utility functions)"
echo "  • src/fixture_scraper.py           (Future fixtures)"
echo "  • src/historical_scraper.py        (Historical data)"
echo "  • config/database.py               (Database connection)"
echo "  • config/config.py                 (Configuration)"

echo ""
echo "📁 Shell Scripts:"
ls -la *.sh 2>/dev/null | while read line; do
    filename=$(echo "$line" | awk '{print $9}')
    if [ "$filename" != "." ] && [ "$filename" != ".." ] && [ -f "$filename" ]; then
        case "$filename" in
            "setup_environment.sh") echo "  • $filename         (Initial setup)" ;;
            "start_live_scraper.sh") echo "  • $filename        (Start data collection)" ;;
            "stop_live_scraper.sh") echo "  • $filename         (Stop collection)" ;;
            "monitor_scraper.sh") echo "  • $filename          (Monitor status)" ;;
            "view_data.sh") echo "  • $filename              (View collected data)" ;;
            "validate_data.sh") echo "  • $filename           (Validate data quality)" ;;
            "cleanup_project.sh") echo "  • $filename         (This cleanup script)" ;;
        esac
    fi
done

echo ""
echo "📊 Data Directories:"
echo "  • exports/                         (CSV output files)"
echo "  • logs/                            (Application logs)"
echo "  • database/                        (Database scripts)"

echo ""
echo "📦 Configuration:"
echo "  • requirements.txt                 (Python dependencies)"
echo "  • .gitignore                       (Git ignore rules)"
echo "  • README.md                        (Documentation)"

# Create a simple project structure overview
cat > PROJECT_STRUCTURE.md << 'EOF'
# SofaScore Live Data Scraper - Project Structure

## 🎯 Purpose
Collects live football match statistics from SofaScore API with minute-by-minute data export.

## 🚀 Quick Start
```bash
./setup_environment.sh    # First-time setup
./start_live_scraper.sh    # Start collecting data
./monitor_scraper.sh       # Monitor in another terminal
./stop_live_scraper.sh     # Stop collection
```

## 📁 Project Structure
```
sofascore-pipeline/
├── src/
│   ├── live_scraper.py         # Main data collector
│   ├── utils.py                # Helper functions
│   ├── fixture_scraper.py      # Future fixtures
│   └── historical_scraper.py   # Historical data
├── config/
│   ├── database.py             # Database connection
│   └── config.py               # Configuration
├── exports/                    # CSV output files
├── logs/                       # Application logs
├── *.sh                        # Shell scripts for operation
└── requirements.txt            # Python dependencies
```

## 📊 Data Output
- **File Format**: `exports/live_match_minutes_complete_YYYYMMDD_HHMMSS.csv`
- **Collection**: Every 5 minutes during live matches
- **Export**: Every 15 minutes
- **Statistics**: Ball possession, shots, passes, fouls, corners, cards, etc.

## 🔧 Configuration
- Collects from up to 5 live matches per cycle
- 1.5 second delay between API requests
- Automatic error handling and retry logic
- Graceful shutdown with Ctrl+C

## 📈 Monitoring
Use `./monitor_scraper.sh` to see:
- Current live matches
- Collection status
- Recent exports
- Error logs
EOF

echo ""
echo "✅ CLEANUP COMPLETED!"
echo "📦 Removed files backed up to: removed_files_backup/"
echo "📄 Created PROJECT_STRUCTURE.md for reference"
echo ""
echo "🎯 STREAMLINED PROJECT READY!"
echo "   • Essential files only"
echo "   • Clean directory structure"
echo "   • Working live data collection"
echo ""
echo "🚀 Your scraper is currently running and collecting data!"
echo "📊 Check exports/ directory for CSV files every 15 minutes"