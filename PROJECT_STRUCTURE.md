# SofaScore Pipeline - Clean Project Structure

## 🎯 Overview
Streamlined live football data collection pipeline with organized structure.

## 🚀 Main Entry Point
```bash
./run.sh    # Interactive menu for all operations
```

## 📁 Directory Structure
```
sofascore-pipeline/
├── run.sh                      # 🎮 Main control script
├── scripts/                    # 📜 All shell scripts
├── src/                        # 🐍 Python source code  
├── config/                     # ⚙️  Configuration files
├── exports/                    # 📊 CSV data exports
├── logs/                       # 📋 Application logs
├── removed_files_backup/       # 🗑️  Backup of removed files
└── requirements.txt            # 📦 Python dependencies
```

## 🔄 Typical Workflow
1. `./run.sh` → **Option 1** (Setup - first time only)
2. `./run.sh` → **Option 2** (Start collecting data)
3. `./run.sh` → **Option 3** (Monitor in new terminal)
4. Let it run for hours/days to collect data
5. `./run.sh` → **Option 4** (View collected data)
6. `./run.sh` → **Option 6** (Stop when done)

## 📊 Data Output
- **File**: `exports/live_match_minutes_complete_TIMESTAMP.csv`
- **Frequency**: New file every 15 minutes
- **Content**: Minute-by-minute match statistics
- **Size**: Typically 5-50 records per file depending on live matches

## 🎯 Clean & Organized
- All scripts in `scripts/` directory
- Single entry point (`run.sh`)
- Removed outdated late_goal functionality
- Clear separation of concerns
- Backup of all removed files
