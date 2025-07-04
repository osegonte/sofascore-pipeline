# Stage 7: Real-Time Analysis and Probability Modeling

This stage implements real-time monitoring and probability calculations for football matches, combining ML predictions with historical analysis to generate betting recommendations.

## 🎯 Overview

Stage 7 monitors live matches and:
- Captures data snapshots at key minutes (59, 60, 69, 70, 79, 80)
- Combines ML predictions from Stage 6 with historical team analysis
- Generates ensemble probability calculations
- Provides betting recommendations with confidence levels
- Sends alerts for high-confidence opportunities

## 🚀 Quick Start

```bash
# Start the real-time analysis system
./stage7_main.sh start

# View system status
./stage7_main.sh status

# Run demo
./demo_stage7.sh

# Run tests
./tests/test_stage7.sh
```

## 📊 Components

### Live Data Monitor
- Continuously monitors live matches
- Captures snapshots at key moments
- Integrates with Stage 6 ML models

### Probability Calculator
- Combines ML predictions with historical analysis
- Generates ensemble probabilities
- Creates betting recommendations

### Scheduler
- Triggers calculations at optimal times
- Manages system health and performance
- Handles alerts and notifications

## 📁 Data Structure

```
stage7/
├── config/          # Configuration files
├── scripts/         # Core scripts
├── data/
│   └── realtime/
│       ├── snapshots/           # Match state snapshots
│       ├── ml_predictions/      # ML model outputs
│       ├── ensemble_predictions/ # Final probability calculations
│       ├── reports/             # Human-readable reports
│       └── alerts/              # High-confidence alerts
├── logs/            # System logs
└── tests/           # Test scripts
```

## ⚙️ Configuration

Edit `config/stage7.conf` to customize:
- Monitoring intervals
- Probability thresholds
- Betting recommendations
- Alert settings

## 📈 Monitoring

- **Live matches**: `data/realtime/live_matches.json`
- **System logs**: `logs/stage7.log`
- **Alerts**: `logs/notifications.log`
- **Performance**: `data/realtime/performance_metrics.json`

## 🎯 Betting Recommendations

The system generates three types of recommendations:
- **BET**: High confidence opportunity
- **CONSIDER**: Medium confidence, smaller stake
- **HOLD**: Low confidence, avoid betting

## 🔧 Troubleshooting

```bash
# Check system status
./stage7_main.sh status

# View recent logs
tail -f logs/stage7.log

# Restart system
./stage7_main.sh restart
```

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Run test script: `tests/test_stage7.sh`
3. Review configuration in `config/stage7.conf`
