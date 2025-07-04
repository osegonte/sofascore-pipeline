#!/bin/bash
# Stage 7 Demo Script

echo "🚀 Stage 7 Real-Time Analysis Demo"
echo "=================================="

# Demo match scenarios
echo "📊 Simulating real-time analysis for demo matches..."

demo_matches=(
    "12345:65:Arsenal:Chelsea:1:0"
    "12346:72:Liverpool:ManCity:2:1" 
    "12347:58:Barcelona:RealMadrid:0:0"
)

for match_data in "${demo_matches[@]}"; do
    IFS=':' read -r match_id minute home away home_score away_score <<< "$match_data"
    
    echo ""
    echo "🏈 Match $match_id: $home vs $away ($home_score-$away_score) at ${minute}'"
    echo "   🤖 Running ML prediction..."
    echo "   📚 Analyzing historical data..."
    echo "   🎯 Calculating ensemble probability..."
    
    # Simulate probability calculation
    python3 -c "
import random
import json

# Simulate realistic probabilities
ml_prob = round(random.uniform(0.3, 0.8), 3)
hist_prob = round(random.uniform(0.2, 0.7), 3)
ensemble_prob = round((ml_prob * 0.7) + (hist_prob * 0.3), 3)
confidence = round(random.uniform(0.4, 0.9), 3)

print(f'   📊 Results:')
print(f'      ML Prediction: {ml_prob:.1%}')
print(f'      Historical: {hist_prob:.1%}') 
print(f'      Ensemble: {ensemble_prob:.1%}')
print(f'      Confidence: {confidence:.1%}')

if ensemble_prob > 0.7 and confidence > 0.6:
    print(f'   ✅ RECOMMENDATION: HIGH CONFIDENCE BET')
elif ensemble_prob > 0.6:
    print(f'   🤔 RECOMMENDATION: CONSIDER BETTING')
else:
    print(f'   ❌ RECOMMENDATION: AVOID BETTING')
"
    
    sleep 2
done

echo ""
echo "🎯 Demo completed! Stage 7 is analyzing matches in real-time."
echo "💡 Next steps:"
echo "   1. Start live monitoring: ./stage7_main.sh start"
echo "   2. View real-time reports in: stage7/data/realtime/reports/"
echo "   3. Monitor alerts in: stage7/logs/notifications.log"
