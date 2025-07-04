#!/bin/bash
# quick_cleanup.sh - Remove redundant and irrelevant files before sharing repo

echo "🧹 Quick Project Cleanup"
echo "========================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cleanup_count=0

echo -e "${BLUE}Removing temporary and backup files...${NC}"

# Remove backup files
find . -name "*.backup*" -type f -delete 2>/dev/null && echo "✅ Backup files removed"
find . -name "*.bak" -type f -delete 2>/dev/null
find . -name "*~" -delete 2>/dev/null

# Remove Python cache
find . -name "*.pyc" -delete 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && echo "✅ Python cache removed"

# Remove system files
find . -name ".DS_Store" -delete 2>/dev/null && echo "✅ System files removed"
find . -name "Thumbs.db" -delete 2>/dev/null

# Remove temporary files
find . -name "*.tmp" -delete 2>/dev/null
find . -name "*.temp" -delete 2>/dev/null

# Remove old log files (keep recent ones)
find . -name "*.log" -mtime +1 -delete 2>/dev/null && echo "✅ Old log files removed"

# Remove duplicate requirements files
rm -f requirements_stage*.txt requirements_ml.txt 2>/dev/null && echo "✅ Duplicate requirements removed"

# Remove redundant scripts
rm -f fix_stage7.sh setup_stage7.sh cleanup_project.sh 2>/dev/null && echo "✅ Setup scripts removed"

# Clean up Stage 7 redundant files
if [ -d "stage7" ]; then
    # Remove old nested structures
    rm -rf stage7/stage7 2>/dev/null
    
    # Remove empty directories
    find stage7 -type d -empty -delete 2>/dev/null
    
    # Remove old PID files
    rm -f stage7/pids/*.pid 2>/dev/null
    
    echo "✅ Stage 7 cleaned"
fi

# Remove large unnecessary files (>10MB that aren't models)
echo -e "${BLUE}Checking for large files...${NC}"
find . -type f -size +10M ! -path "./data/models/*" ! -path "./venv/*" -exec ls -lh {} \; 2>/dev/null | while read -r line; do
    echo "⚠️  Large file found: $line"
done

# Clean up virtual environment cache
if [ -d "venv" ]; then
    find venv -name "*.pyc" -delete 2>/dev/null
    rm -rf venv/lib/python*/site-packages/pip/_internal/cache 2>/dev/null
    echo "✅ Virtual environment cache cleaned"
fi

# Remove empty directories
find . -type d -empty -delete 2>/dev/null

# Show final status
echo ""
echo -e "${GREEN}🎉 Cleanup completed!${NC}"
echo ""
echo "📊 Current project structure:"
echo "├── src/                    # Core pipeline"
echo "├── data/models/            # ML models (keep)"
echo "├── stage7/                 # Real-time analysis"
echo "├── venv/                   # Python environment"
echo "├── demo_training_dataset.csv"
echo "├── requirements_unified.txt"
echo "├── stage7.sh               # Main runner"
echo "└── README.md"
echo ""

# Check final size
total_size=$(du -sh . 2>/dev/null | cut -f1)
echo -e "📦 Total project size: ${YELLOW}$total_size${NC}"

echo ""
echo "🚀 Project is now clean and ready to share!"
echo "💡 Key files to focus on:"
echo "   - stage7.sh (main Stage 7 runner)"
echo "   - data/models/saved_models/ (ML models)"
echo "   - demo_training_dataset.csv (training data)"
echo "   - stage7/data/realtime/ (live predictions)"