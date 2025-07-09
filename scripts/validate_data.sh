#!/bin/bash
# validate_data.sh - Validate collected data against expected values

echo "🔍 SofaScore Data Validation"
echo "============================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Find most recent data file
recent_file=$(find exports -name "live_match_minutes_complete_*.csv" -mtime -1 2>/dev/null | sort -r | head -1)

if [ -z "$recent_file" ]; then
    echo "❌ No recent data files found"
    echo "   Run the live scraper first: ./start_live_scraper.sh"
    exit 1
fi

echo "📁 Validating: $(basename "$recent_file")"
echo ""

python -c "
import pandas as pd
import sys

def validate_data(filepath):
    try:
        df = pd.read_csv(filepath)
        
        print('🔍 RUNNING VALIDATION TESTS')
        print('============================')
        
        total_tests = 0
        passed_tests = 0
        
        # Test 1: Basic structure
        total_tests += 1
        if len(df) > 0 and len(df.columns) > 50:  # Should have many statistics
            print('✅ Test 1: Data structure - PASSED')
            passed_tests += 1
        else:
            print('❌ Test 1: Data structure - FAILED (insufficient data/columns)')
        
        # Test 2: Possession validation
        total_tests += 1
        if 'ball_possession_home' in df.columns and 'ball_possession_away' in df.columns:
            possession_sums = df['ball_possession_home'] + df['ball_possession_away']
            valid_possession = ((possession_sums >= 95) & (possession_sums <= 105)).sum()
            possession_rate = (valid_possession / len(df)) * 100
            
            if possession_rate > 80:
                print(f'✅ Test 2: Possession validation - PASSED ({possession_rate:.1f}% valid)')
                passed_tests += 1
            else:
                print(f'❌ Test 2: Possession validation - FAILED ({possession_rate:.1f}% valid)')
        else:
            print('⚠️  Test 2: Possession validation - SKIPPED (missing columns)')
        
        # Test 3: Shot consistency
        total_tests += 1
        if all(col in df.columns for col in ['total_shots_home', 'shots_on_target_home', 'total_shots_away', 'shots_on_target_away']):
            home_valid = (df['shots_on_target_home'] <= df['total_shots_home']).sum()
            away_valid = (df['shots_on_target_away'] <= df['total_shots_away']).sum()
            shot_consistency = ((home_valid + away_valid) / (len(df) * 2)) * 100
            
            if shot_consistency > 95:
                print(f'✅ Test 3: Shot consistency - PASSED ({shot_consistency:.1f}% valid)')
                passed_tests += 1
            else:
                print(f'❌ Test 3: Shot consistency - FAILED ({shot_consistency:.1f}% valid)')
        else:
            print('⚠️  Test 3: Shot consistency - SKIPPED (missing columns)')
        
        # Test 4: Minute progression
        total_tests += 1
        if 'match_minute' in df.columns:
            minute_range = df['match_minute'].max() - df['match_minute'].min()
            if minute_range > 10:  # Should span multiple minutes
                print(f'✅ Test 4: Minute progression - PASSED (span: {minute_range} minutes)')
                passed_tests += 1
            else:
                print(f'❌ Test 4: Minute progression - FAILED (span: {minute_range} minutes)')
        else:
            print('⚠️  Test 4: Minute progression - SKIPPED (missing column)')
        
        # Test 5: Data freshness
        total_tests += 1
        if 'collection_timestamp' in df.columns:
            df['collection_timestamp'] = pd.to_datetime(df['collection_timestamp'])
            latest_data = df['collection_timestamp'].max()
            hours_old = (pd.Timestamp.now() - latest_data).total_seconds() / 3600
            
            if hours_old < 24:
                print(f'✅ Test 5: Data freshness - PASSED ({hours_old:.1f} hours old)')
                passed_tests += 1
            else:
                print(f'❌ Test 5: Data freshness - FAILED ({hours_old:.1f} hours old)')
        else:
            print('⚠️  Test 5: Data freshness - SKIPPED (missing column)')
        
        # Test 6: Statistics completeness
        total_tests += 1
        expected_stats = [
            'ball_possession_home', 'ball_possession_away',
            'total_shots_home', 'total_shots_away',
            'passes_home', 'passes_away',
            'fouls_home', 'fouls_away'
        ]
        
        present_stats = sum(1 for stat in expected_stats if stat in df.columns)
        completeness_rate = (present_stats / len(expected_stats)) * 100
        
        if completeness_rate > 80:
            print(f'✅ Test 6: Statistics completeness - PASSED ({completeness_rate:.1f}%)')
            passed_tests += 1
        else:
            print(f'❌ Test 6: Statistics completeness - FAILED ({completeness_rate:.1f}%)')
        
        print()
        print('📊 VALIDATION SUMMARY')
        print('====================')
        print(f'Tests passed: {passed_tests}/{total_tests}')
        print(f'Success rate: {(passed_tests/total_tests)*100:.1f}%')
        
        if passed_tests == total_tests:
            print('🎉 ALL TESTS PASSED - Data quality excellent!')
            return 0
        elif passed_tests >= total_tests * 0.8:
            print('🟨 MOSTLY PASSED - Data quality good with minor issues')
            return 0
        else:
            print('❌ TESTS FAILED - Data quality needs improvement')
            return 1
    
    except Exception as e:
        print(f'❌ Validation error: {e}')
        return 1

sys.exit(validate_data('$recent_file'))
"

validation_result=$?

echo ""
echo "💡 RECOMMENDATIONS:"

if [ $validation_result -eq 0 ]; then
    echo "   ✅ Data quality is good - ready for analysis"
    echo "   📈 Continue monitoring to collect more data"
    echo "   🔄 Consider running historical collection for more data"
else
    echo "   🔧 Review scraper configuration"
    echo "   🌐 Check SofaScore API endpoint stability"
    echo "   📋 Review logs for errors: logs/pipeline_*.log"
fi

echo ""
echo "📁 Data file: $recent_file"
echo "📊 Use './view_data.sh' to explore the data in detail"
