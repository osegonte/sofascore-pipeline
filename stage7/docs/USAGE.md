# Stage 7 Usage Guide

## Starting the System

```bash
# Start all Stage 7 components
./stage7_main.sh start

# This starts:
# - Live data monitor
# - Probability scheduler
# - Alert system
```

## Monitoring Live Matches

The system automatically:
1. Discovers live matches from SofaScore
2. Filters for matches in late stages (55+ minutes)
3. Captures snapshots at key minutes
4. Calculates probabilities every 15-60 seconds

## Understanding Probability Outputs

### Ensemble Predictions
- **goal_next_1min**: Probability of goal in next minute
- **goal_next_5min**: Probability of goal in next 5 minutes  
- **goal_next_15min**: Probability of goal in next 15 minutes

### Confidence Levels
- **HIGH** (0.6+): Strong recommendation
- **MEDIUM** (0.4-0.6): Consider with caution
- **LOW** (<0.4): Avoid betting

### Betting Recommendations
- **BET**: High probability + high confidence
- **CONSIDER**: Medium probability or confidence
- **HOLD**: Low probability or confidence

## Reading Reports

Reports are generated in `data/realtime/reports/`:

```
🏈 MATCH ANALYSIS REPORT
========================
Match: Arsenal vs Chelsea
Current Score: 1-0
Minute: 65

📊 GOAL PROBABILITIES
=====================
Next 1 minute:  12.3%
Next 5 minutes: 34.7%  
Next 15 minutes: 58.2%

Confidence Level: 71.4% (HIGH)

🎯 BETTING RECOMMENDATIONS
==========================
Action: BET
✅ RECOMMENDED BETS:
  • Goal in next 15 minutes - 58.2%

💡 REASONING:
  • High probability (58.2%) of goal in next 15 minutes
```

## Alert System

Alerts are generated for:
- High confidence betting opportunities (60%+ confidence)
- Immediate opportunities (next minute predictions)
- Probabilities above 80%

Alerts appear in:
- Terminal output (if running interactively)
- `logs/notifications.log`
- `data/realtime/alerts/` directory

## Integration with Stage 6

Stage 7 uses ML models from Stage 6:
- Loads best performing models for each target
- Applies same preprocessing (feature selection, scaling)
- Generates predictions for current match state
- Combines with historical analysis

## Performance Monitoring

Monitor system performance:

```bash
# View performance metrics
cat data/realtime/performance_metrics.json

# Check active processes
./stage7_main.sh status

# View system health
tail logs/stage7.log | grep HEALTH
```

## Customization

### Key Minutes
Edit `config/stage7_config.sh`:
```bash
export KEY_MINUTES="59 60 69 70 79 80"
```

### Probability Weights
Adjust ML vs Historical weighting:
```bash
export ML_WEIGHT=0.7
export HISTORICAL_WEIGHT=0.3
```

### Betting Thresholds
Modify recommendation thresholds:
```bash
export HIGH_PROB_THRESHOLD=0.7
export HIGH_CONFIDENCE_THRESHOLD=0.6
```
