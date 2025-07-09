# SofaScore Live Data Pipeline

A streamlined pipeline for collecting live football match statistics from SofaScore API.

## 🚀 Quick Start

```bash
# Make main script executable
chmod +x run.sh

# Run the interactive menu
./run.sh
```

## 📁 Project Structure

```
sofascore-pipeline/
├── run.sh                      # Main control script
├── scripts/                    # All shell scripts
│   ├── setup_environment.sh    # Environment setup
│   ├── start_live_scraper.sh   # Start collection
│   ├── stop_live_scraper.sh    # Stop collection
│   ├── monitor_scraper.sh      # Monitor status
│   ├── view_data.sh            # View data
│   └── validate_data.sh        # Validate quality
├── src/                        # Python source code
│   ├── live_scraper.py         # Main data collector
│   ├── utils.py                # Helper functions
│   ├── fixture_scraper.py      # Fixture collection
│   └── historical_scraper.py   # Historical data
├── config/                     # Configuration
│   ├── database.py             # Database setup
│   └── config.py               # Settings
├── exports/                    # CSV output files
├── logs/                       # Application logs
└── requirements.txt            # Python dependencies
```

## 📊 Data Collection

- **Frequency**: Every 5 minutes during live matches
- **Export**: CSV files every 15 minutes
- **Format**: `exports/live_match_minutes_complete_YYYYMMDD_HHMMSS.csv`
- **Statistics**: Possession, shots, passes, fouls, corners, cards, and more

## 🎯 Features

✅ **Live Data Collection**: Real-time statistics from ongoing matches  
✅ **Comprehensive Stats**: Ball possession, shots, passes, duels, defending, goalkeeping  
✅ **CSV Export**: Clean, timestamped data files  
✅ **Error Handling**: Automatic retry and graceful error recovery  
✅ **Monitoring**: Real-time status dashboard  
✅ **Data Validation**: Quality checks and completeness verification  

## 🔧 Usage

1. **First Time Setup**: `./run.sh` → Option 1
2. **Start Collection**: `./run.sh` → Option 2  
3. **Monitor Progress**: `./run.sh` → Option 3 (in new terminal)
4. **View Data**: `./run.sh` → Option 4
5. **Stop Collection**: `./run.sh` → Option 6

## 📈 Output Data

Each CSV contains minute-by-minute records with:
- Match information (teams, competition, venue, score)
- Ball possession percentages
- Shot statistics (total, on target, off target, blocked)
- Passing statistics (total passes, accuracy)
- Defensive statistics (fouls, tackles, cards)
- Goalkeeping statistics (saves, goal kicks)

## 🛠️ Requirements

- Python 3.7+
- PostgreSQL (optional - for database storage)
- Internet connection for SofaScore API access

## 📝 Notes

- Designed for continuous operation during live matches
- Handles API rate limiting automatically
- Exports data regularly to prevent loss
- Includes comprehensive logging for troubleshooting
