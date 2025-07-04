# Stage 8: Dashboard & Betting Recommendations

Modern web-based dashboard that transforms Stage 7's technical ML outputs into actionable betting insights.

## 🎯 Features

- **Real-time Live Matches**: Monitor matches in late stages (55+ minutes)
- **Probability Visualization**: Clear displays of 1min, 5min, 15min goal probabilities
- **Betting Signals**: BUY/CONSIDER/HOLD recommendations with confidence levels
- **High-Confidence Alerts**: Automatic notifications for betting opportunities
- **WebSocket Updates**: Real-time data streaming every 30 seconds
- **Performance Tracking**: System metrics and ROI analysis

## 🚀 Quick Start

```bash
# Start the dashboard (from project root)
./stage8.sh start

# View status
./stage8.sh status

# Test integration
./stage8.sh test
```

## 🌐 Access Points

- **Dashboard**: http://localhost:8008
- **API Documentation**: http://localhost:8008/docs
- **WebSocket**: ws://localhost:8008/ws

## 📊 Dashboard Components

### Live Matches Panel
- Team names and current scores
- Live minute indicator
- Probability meters for different timeframes
- Confidence circles showing prediction reliability
- Clear betting recommendations

### Alerts Panel
- High-confidence betting opportunities
- Immediate action alerts
- Timestamp and probability details

### Performance Panel
- Active matches count
- Predictions generated today
- Alert rate and average confidence
- Real-time performance chart

## 🔗 Integration with Stage 7

Stage 8 reads data from:
- `stage7/data/realtime/live_matches.json` - Live match data
- `stage7/data/realtime/ensemble_predictions/` - ML predictions
- `stage7/data/realtime/alerts/` - High-confidence alerts

## ⚙️ Configuration

Edit `config/dashboard_config.json` to customize:
- Update intervals
- Confidence thresholds
- UI settings
- Betting parameters

## 🧪 Development

```bash
# Test backend integration
python3 stage8_backend.py test

# Setup development environment
python3 stage8_backend.py setup

# Start with debug mode
DEBUG=true ./stage8.sh start
```

## 📱 Mobile Support

The dashboard is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones

## 🔧 Troubleshooting

1. **Dashboard won't start**: Check if port 8008 is available
2. **No live data**: Ensure Stage 7 is running (`./stage7.sh status`)
3. **WebSocket errors**: Check firewall settings for port 8008
4. **Missing predictions**: Verify Stage 6 models are trained

## 📈 Usage Scenarios

### High-Confidence Betting
When confidence ≥ 70% and probability ≥ 70%:
- Dashboard shows "STRONG BUY" signal
- Alert notification appears
- Recommended stake size displayed

### Medium-Confidence Opportunities
When confidence ≥ 50% and probability ≥ 60%:
- Dashboard shows "CONSIDER" signal
- Smaller recommended stake
- Additional context provided

### Hold Signals
When confidence < 50% or probability < 40%:
- Dashboard shows "HOLD" signal
- Avoid betting recommendation
- Wait for better opportunities

## 🎯 Betting Strategy Integration

The dashboard is optimized for:
- **60th-70th minute scenarios** (highest prediction accuracy)
- **Late-game goal predictions** (most profitable opportunities)
- **Risk-adjusted position sizing** (based on confidence levels)
- **Real-time decision making** (30-second update cycles)

## 🔍 API Endpoints

- `GET /api/live-matches` - Current live matches
- `GET /api/alerts` - Active alerts
- `GET /api/predictions/{match_id}` - Match predictions
- `GET /api/system-status` - System health
- `WebSocket /ws` - Real-time updates

## 🎨 Customization

The dashboard supports:
- Dark/light themes
- Custom confidence thresholds
- Adjustable update intervals
- Sound alerts (optional)
- Export functionality

Built for the SofaScore Pipeline Stage 8 🚀
