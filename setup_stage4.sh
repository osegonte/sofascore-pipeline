#!/bin/bash

# SofaScore Data Pipeline - Stage 4: Testing and Validation Setup
# Creates comprehensive testing framework for data accuracy and reliability

echo "SofaScore Pipeline - Stage 4: Testing & Validation Setup"
echo "======================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Create testing directory structure
echo "📁 Creating testing directory structure..."
mkdir -p tests/{unit,integration,validation,performance,data_quality}
mkdir -p tests/fixtures/sample_data
mkdir -p tests/reports
mkdir -p logs/tests

# Create test configuration
echo "⚙️  Creating test configuration..."
cat > tests/test_config.py << 'EOF'
"""
Test configuration for SofaScore pipeline validation
"""
import os
from datetime import datetime, timedelta

# Test Database Configuration
TEST_DB_NAME = "sofascore_test"
TEST_EXPORT_DIR = "tests/fixtures/sample_data"
TEST_REPORTS_DIR = "tests/reports"

# Data Validation Thresholds
VALIDATION_THRESHOLDS = {
    'goal_timestamp_accuracy_seconds': 60,  # Goals within 1 minute tolerance
    'possession_percentage_tolerance': 5.0,  # 5% tolerance for possession
    'shots_count_tolerance': 2,  # +/- 2 shots tolerance
    'fixture_time_accuracy_minutes': 15,  # 15 minute tolerance for kickoff times
    'minimum_data_completeness': 0.85,  # 85% data completeness required
    'late_goal_percentage_range': (5.0, 25.0),  # Expected late goal percentage range
    'max_api_response_time_seconds': 10.0,  # Maximum acceptable API response time
    'database_query_timeout_seconds': 30.0  # Maximum database query time
}

# Reference Data Sources
REFERENCE_SOURCES = {
    'sofascore_ui': 'https://www.sofascore.com',
    'backup_api': None,  # Could add ESPN, BBC Sport, etc.
}

# Test Match IDs (known completed matches for validation)
REFERENCE_MATCH_IDS = [
    # Add specific match IDs here after identifying reliable test cases
]

# Performance Test Parameters
PERFORMANCE_TEST_CONFIG = {
    'concurrent_matches': 5,
    'test_duration_minutes': 10,
    'max_memory_usage_mb': 512,
    'max_cpu_percentage': 80
}

# Reliability Test Configuration
RELIABILITY_TEST_CONFIG = {
    'test_cycles': 50,
    'acceptable_failure_rate': 0.05,  # 5% failure rate acceptable
    'retry_attempts': 3,
    'backoff_seconds': [1, 2, 5]
}
EOF

# Create comprehensive data accuracy validator
echo "🔍 Creating data accuracy validator..."
cat > tests/validation/test_data_accuracy.py << 'EOF'
#!/usr/bin/env python3
"""
Comprehensive data accuracy validation for SofaScore pipeline
Tests scraped data against reference sources and known standards
"""

import sys
import os
import unittest
import pandas as pd
from datetime import datetime, timedelta
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.live_scraper import LiveMatchScraper
from src.historical_scraper import HistoricalScraper
from src.fixture_scraper import FixtureScraper
from config.database import engine
from tests.test_config import VALIDATION_THRESHOLDS, REFERENCE_MATCH_IDS
from sqlalchemy import text

class DataAccuracyValidator(unittest.TestCase):
    """Comprehensive data accuracy validation suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.live_scraper = LiveMatchScraper()
        cls.historical_scraper = HistoricalScraper()
        cls.fixture_scraper = FixtureScraper()
        cls.validation_results = {}
        
    def test_goal_timestamp_accuracy(self):
        """Test goal timestamp accuracy against database records"""
        print("\n🎯 Testing goal timestamp accuracy...")
        
        try:
            with engine.connect() as conn:
                # Get recent goals with match context
                result = conn.execute(text("""
                    SELECT g.goal_id, g.exact_timestamp, g.added_time, g.total_minute,
                           g.scoring_player, g.team_side, m.home_team, m.away_team,
                           m.competition, g.is_late_goal, g.time_interval
                    FROM goal_events g
                    JOIN live_matches m ON g.match_id = m.match_id
                    ORDER BY g.total_minute
                    LIMIT 20
                """))
                
                goals = result.fetchall()
                
                if not goals:
                    self.skipTest("No goals found in database for validation")
                
                # Validate goal timing logic
                timing_errors = []
                for goal in goals:
                    goal_id, timestamp, added_time, total_minute = goal[0], goal[1], goal[2], goal[3]
                    is_late_goal, time_interval = goal[9], goal[10]
                    
                    # Check total minute calculation
                    calculated_total = timestamp + (added_time or 0)
                    if calculated_total != total_minute:
                        timing_errors.append(f"Goal {goal_id}: Total minute mismatch")
                    
                    # Check late goal classification
                    expected_late = calculated_total >= 75
                    if bool(is_late_goal) != expected_late:
                        timing_errors.append(f"Goal {goal_id}: Late goal classification error")
                    
                    # Check time interval classification
                    expected_interval = self._get_expected_interval(calculated_total)
                    if time_interval != expected_interval:
                        timing_errors.append(f"Goal {goal_id}: Time interval mismatch")
                
                self.validation_results['goal_timestamp_accuracy'] = {
                    'total_goals_tested': len(goals),
                    'timing_errors': len(timing_errors),
                    'accuracy_percentage': ((len(goals) - len(timing_errors)) / len(goals)) * 100,
                    'errors': timing_errors
                }
                
                print(f"   ✓ Tested {len(goals)} goals")
                print(f"   ✓ Timing accuracy: {self.validation_results['goal_timestamp_accuracy']['accuracy_percentage']:.1f}%")
                
                # Assert high accuracy
                self.assertLess(len(timing_errors), len(goals) * 0.05, 
                               f"Too many timing errors: {timing_errors}")
                
        except Exception as e:
            self.fail(f"Goal timestamp validation failed: {e}")
    
    def test_team_statistics_consistency(self):
        """Test team statistics for logical consistency"""
        print("\n📊 Testing team statistics consistency...")
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT ts.match_id, ts.team_side, ts.possession_percentage,
                           ts.shots_on_target, ts.total_shots, ts.corners,
                           ts.fouls, ts.yellow_cards, ts.red_cards,
                           m.home_team, m.away_team, m.competition
                    FROM team_statistics ts
                    JOIN live_matches m ON ts.match_id = m.match_id
                    ORDER BY ts.match_id, ts.team_side
                    LIMIT 50
                """))
                
                stats = result.fetchall()
                
                if not stats:
                    self.skipTest("No team statistics found for validation")
                
                consistency_errors = []
                match_stats = {}
                
                # Group by match
                for stat in stats:
                    match_id = stat[0]
                    if match_id not in match_stats:
                        match_stats[match_id] = {'home': None, 'away': None}
                    match_stats[match_id][stat[1]] = stat
                
                # Validate consistency
                for match_id, teams in match_stats.items():
                    if teams['home'] and teams['away']:
                        home_stats, away_stats = teams['home'], teams['away']
                        
                        # Check possession adds to ~100%
                        home_poss = home_stats[2] or 0
                        away_poss = away_stats[2] or 0
                        if abs((home_poss + away_poss) - 100) > 10:  # 10% tolerance
                            consistency_errors.append(f"Match {match_id}: Possession doesn't add to 100%")
                        
                        # Check shots on target <= total shots
                        for side, stat in [('home', home_stats), ('away', away_stats)]:
                            shots_on_target = stat[3] or 0
                            total_shots = stat[4] or 0
                            if shots_on_target > total_shots:
                                consistency_errors.append(f"Match {match_id} {side}: Shots on target > total shots")
                
                self.validation_results['team_statistics_consistency'] = {
                    'matches_tested': len(match_stats),
                    'consistency_errors': len(consistency_errors),
                    'accuracy_percentage': ((len(match_stats) - len(consistency_errors)) / len(match_stats)) * 100 if match_stats else 0,
                    'errors': consistency_errors
                }
                
                print(f"   ✓ Tested {len(match_stats)} matches")
                print(f"   ✓ Consistency: {self.validation_results['team_statistics_consistency']['accuracy_percentage']:.1f}%")
                
                self.assertLess(len(consistency_errors), len(match_stats) * 0.1, 
                               f"Too many consistency errors: {consistency_errors}")
                
        except Exception as e:
            self.fail(f"Team statistics validation failed: {e}")
    
    def test_fixture_scheduling_accuracy(self):
        """Test fixture scheduling data accuracy"""
        print("\n📅 Testing fixture scheduling accuracy...")
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT fixture_id, home_team, away_team, kickoff_time, 
                           kickoff_date, tournament, status, venue
                    FROM fixtures
                    WHERE kickoff_date >= CURRENT_DATE
                    ORDER BY kickoff_date, kickoff_time
                    LIMIT 30
                """))
                
                fixtures = result.fetchall()
                
                if not fixtures:
                    self.skipTest("No future fixtures found for validation")
                
                scheduling_errors = []
                
                for fixture in fixtures:
                    fixture_id, home_team, away_team = fixture[0], fixture[1], fixture[2]
                    kickoff_time, kickoff_date = fixture[3], fixture[4]
                    
                    # Check required fields
                    if not all([home_team, away_team, kickoff_date]):
                        scheduling_errors.append(f"Fixture {fixture_id}: Missing required fields")
                    
                    # Check team names are different
                    if home_team == away_team:
                        scheduling_errors.append(f"Fixture {fixture_id}: Same home and away team")
                    
                    # Check date is in future (for upcoming fixtures)
                    if kickoff_date and kickoff_date < datetime.now().date():
                        # Only error if status indicates it's upcoming
                        if not any(word in str(fixture[6]).lower() for word in ['finished', 'postponed', 'cancelled']):
                            scheduling_errors.append(f"Fixture {fixture_id}: Past date for upcoming match")
                
                self.validation_results['fixture_scheduling_accuracy'] = {
                    'fixtures_tested': len(fixtures),
                    'scheduling_errors': len(scheduling_errors),
                    'accuracy_percentage': ((len(fixtures) - len(scheduling_errors)) / len(fixtures)) * 100,
                    'errors': scheduling_errors
                }
                
                print(f"   ✓ Tested {len(fixtures)} fixtures")
                print(f"   ✓ Scheduling accuracy: {self.validation_results['fixture_scheduling_accuracy']['accuracy_percentage']:.1f}%")
                
                self.assertLess(len(scheduling_errors), len(fixtures) * 0.05, 
                               f"Too many scheduling errors: {scheduling_errors}")
                
        except Exception as e:
            self.fail(f"Fixture scheduling validation failed: {e}")
    
    def test_data_completeness(self):
        """Test overall data completeness"""
        print("\n📋 Testing data completeness...")
        
        try:
            with engine.connect() as conn:
                # Check data completeness across tables
                completeness_metrics = {}
                
                # Goal events completeness
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_goals,
                        COUNT(scoring_player) as goals_with_player,
                        COUNT(team_side) as goals_with_team_side,
                        COUNT(exact_timestamp) as goals_with_timestamp
                    FROM goal_events
                """))
                
                goal_data = result.fetchone()
                if goal_data and goal_data[0] > 0:
                    completeness_metrics['goal_events'] = {
                        'player_completeness': (goal_data[1] / goal_data[0]) * 100,
                        'team_side_completeness': (goal_data[2] / goal_data[0]) * 100,
                        'timestamp_completeness': (goal_data[3] / goal_data[0]) * 100
                    }
                
                # Match details completeness
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_matches,
                        COUNT(home_team) as matches_with_home_team,
                        COUNT(away_team) as matches_with_away_team,
                        COUNT(competition) as matches_with_competition
                    FROM live_matches
                """))
                
                match_data = result.fetchone()
                if match_data and match_data[0] > 0:
                    completeness_metrics['live_matches'] = {
                        'home_team_completeness': (match_data[1] / match_data[0]) * 100,
                        'away_team_completeness': (match_data[2] / match_data[0]) * 100,
                        'competition_completeness': (match_data[3] / match_data[0]) * 100
                    }
                
                self.validation_results['data_completeness'] = completeness_metrics
                
                # Check minimum completeness threshold
                min_completeness = VALIDATION_THRESHOLDS['minimum_data_completeness'] * 100
                
                for table, metrics in completeness_metrics.items():
                    for field, completeness in metrics.items():
                        print(f"   ✓ {table}.{field}: {completeness:.1f}% complete")
                        self.assertGreaterEqual(completeness, min_completeness, 
                                              f"{table}.{field} completeness too low: {completeness:.1f}%")
                
        except Exception as e:
            self.fail(f"Data completeness validation failed: {e}")
    
    def test_goal_timing_analysis_accuracy(self):
        """Test goal timing analysis calculations"""
        print("\n⏰ Testing goal timing analysis accuracy...")
        
        try:
            with engine.connect() as conn:
                # Test late goal analysis
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_goals,
                        COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals_computed,
                        COUNT(*) FILTER (WHERE total_minute >= 75) as late_goals_manual,
                        AVG(total_minute) as avg_goal_minute
                    FROM goal_events
                    WHERE total_minute IS NOT NULL
                """))
                
                analysis_data = result.fetchone()
                
                if not analysis_data or analysis_data[0] == 0:
                    self.skipTest("No goals with timing data found")
                
                total_goals = analysis_data[0]
                late_goals_computed = analysis_data[1]
                late_goals_manual = analysis_data[2]
                avg_goal_minute = analysis_data[3]
                
                # Verify late goal calculation consistency
                self.assertEqual(late_goals_computed, late_goals_manual, 
                               "Late goal computation inconsistency")
                
                # Check late goal percentage is reasonable
                late_goal_percentage = (late_goals_computed / total_goals) * 100
                min_pct, max_pct = VALIDATION_THRESHOLDS['late_goal_percentage_range']
                
                self.validation_results['goal_timing_analysis'] = {
                    'total_goals': total_goals,
                    'late_goals': late_goals_computed,
                    'late_goal_percentage': late_goal_percentage,
                    'average_goal_minute': float(avg_goal_minute),
                    'percentage_within_expected_range': min_pct <= late_goal_percentage <= max_pct
                }
                
                print(f"   ✓ {total_goals} goals analyzed")
                print(f"   ✓ {late_goals_computed} late goals ({late_goal_percentage:.1f}%)")
                print(f"   ✓ Average goal minute: {avg_goal_minute:.1f}")
                
                # Reasonable range check (not strict assertion as it depends on data)
                if not (min_pct <= late_goal_percentage <= max_pct):
                    print(f"   ⚠️  Late goal percentage outside expected range: {late_goal_percentage:.1f}%")
                
        except Exception as e:
            self.fail(f"Goal timing analysis validation failed: {e}")
    
    def _get_expected_interval(self, total_minute):
        """Get expected time interval for a given minute"""
        if total_minute <= 15:
            return '0-15'
        elif total_minute <= 30:
            return '16-30'
        elif total_minute <= 45:
            return '31-45'
        elif total_minute <= 60:
            return '46-60'
        elif total_minute <= 75:
            return '61-75'
        elif total_minute <= 90:
            return '76-90'
        else:
            return '90+'
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Generate validation report"""
        cls._generate_validation_report()
    
    @classmethod
    def _generate_validation_report(cls):
        """Generate comprehensive validation report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/reports/data_accuracy_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Data Accuracy Validation Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for test_name, results in cls.validation_results.items():
                f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                
                if isinstance(results, dict):
                    for key, value in results.items():
                        if key != 'errors':
                            f.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                    
                    if 'errors' in results and results['errors']:
                        f.write(f"\n### Errors ({len(results['errors'])})\n\n")
                        for error in results['errors'][:10]:  # Limit to first 10 errors
                            f.write(f"- {error}\n")
                        if len(results['errors']) > 10:
                            f.write(f"- ... and {len(results['errors']) - 10} more errors\n")
                
                f.write("\n")
        
        print(f"\n📄 Validation report saved: {report_file}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
EOF

# Create reliability testing framework
echo "🔄 Creating reliability testing framework..."
cat > tests/validation/test_reliability.py << 'EOF'
#!/usr/bin/env python3
"""
Reliability testing for SofaScore pipeline
Tests pipeline stability, error handling, and consistency
"""

import sys
import os
import unittest
import time
import threading
import concurrent.futures
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.live_scraper import LiveMatchScraper
from src.fixture_scraper import FixtureScraper
from src.historical_scraper import HistoricalScraper
from tests.test_config import RELIABILITY_TEST_CONFIG, PERFORMANCE_TEST_CONFIG

class ReliabilityTester(unittest.TestCase):
    """Comprehensive reliability testing suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up reliability test environment"""
        cls.live_scraper = LiveMatchScraper()
        cls.fixture_scraper = FixtureScraper()
        cls.historical_scraper = HistoricalScraper()
        cls.reliability_results = {}
    
    def test_api_consistency(self):
        """Test API response consistency across multiple calls"""
        print("\n🔄 Testing API consistency...")
        
        test_cycles = RELIABILITY_TEST_CONFIG['test_cycles']
        failures = []
        response_times = []
        
        for i in range(min(test_cycles, 10)):  # Limit to 10 for CI/CD
            start_time = time.time()
            
            try:
                # Test fixture endpoint consistency
                fixtures = self.fixture_scraper.get_fixtures_by_date(
                    datetime.now().strftime('%Y-%m-%d')
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Basic validation
                if not isinstance(fixtures, list):
                    failures.append(f"Cycle {i}: Invalid response type")
                
                # Check response time
                if response_time > RELIABILITY_TEST_CONFIG.get('max_response_time', 30):
                    failures.append(f"Cycle {i}: Slow response time: {response_time:.2f}s")
                
            except Exception as e:
                failures.append(f"Cycle {i}: Exception: {str(e)}")
                response_times.append(float('inf'))
            
            time.sleep(1)  # Rate limiting
        
        failure_rate = len(failures) / min(test_cycles, 10)
        avg_response_time = sum(r for r in response_times if r != float('inf')) / len([r for r in response_times if r != float('inf')]) if response_times else 0
        
        self.reliability_results['api_consistency'] = {
            'test_cycles': min(test_cycles, 10),
            'failures': len(failures),
            'failure_rate': failure_rate,
            'average_response_time': avg_response_time,
            'max_response_time': max(r for r in response_times if r != float('inf')) if response_times else 0
        }
        
        print(f"   ✓ Tested {min(test_cycles, 10)} API calls")
        print(f"   ✓ Failure rate: {failure_rate:.1%}")
        print(f"   ✓ Average response time: {avg_response_time:.2f}s")
        
        acceptable_failure_rate = RELIABILITY_TEST_CONFIG['acceptable_failure_rate']
        self.assertLessEqual(failure_rate, acceptable_failure_rate, 
                           f"API failure rate too high: {failure_rate:.1%}")
    
    def test_concurrent_scraping(self):
        """Test concurrent scraping reliability"""
        print("\n🚀 Testing concurrent scraping...")
        
        concurrent_matches = min(PERFORMANCE_TEST_CONFIG['concurrent_matches'], 3)
        results = []
        
        def scrape_fixtures():
            """Scrape fixtures in separate thread"""
            try:
                start_time = time.time()
                fixtures = self.fixture_scraper.get_upcoming_fixtures(days_ahead=3)
                end_time = time.time()
                return {
                    'success': True,
                    'fixture_count': len(fixtures),
                    'duration': end_time - start_time,
                    'error': None
                }
            except Exception as e:
                return {
                    'success': False,
                    'fixture_count': 0,
                    'duration': 0,
                    'error': str(e)
                }
        
        # Run concurrent tests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_matches) as executor:
            futures = [executor.submit(scrape_fixtures) for _ in range(concurrent_matches)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        successful_runs = sum(1 for r in results if r['success'])
        failure_rate = (len(results) - successful_runs) / len(results)
        avg_duration = sum(r['duration'] for r in results if r['success']) / successful_runs if successful_runs > 0 else 0
        
        self.reliability_results['concurrent_scraping'] = {
            'concurrent_workers': concurrent_matches,
            'total_runs': len(results),
            'successful_runs': successful_runs,
            'failure_rate': failure_rate,
            'average_duration': avg_duration,
            'errors': [r['error'] for r in results if not r['success']]
        }
        
        print(f"   ✓ Ran {len(results)} concurrent scraping tasks")
        print(f"   ✓ Success rate: {(successful_runs/len(results)):.1%}")
        print(f"   ✓ Average duration: {avg_duration:.2f}s")
        
        self.assertLessEqual(failure_rate, 0.2, f"Concurrent scraping failure rate too high: {failure_rate:.1%}")
    
    def test_data_export_reliability(self):
        """Test CSV export reliability and completeness"""
        print("\n📊 Testing data export reliability...")
        
        export_results = []
        
        try:
            # Test small fixture export
            fixtures = self.fixture_scraper.get_upcoming_fixtures(days_ahead=2)
            
            if fixtures:
                fixtures_df = self.fixture_scraper.to_dataframe(fixtures)
                test_file = "tests/fixtures/sample_data/test_export.csv"
                
                # Export test
                start_time = time.time()
                fixtures_df.to_csv(test_file, index=False)
                export_time = time.time() - start_time
                
                # Re-import test
                start_time = time.time()
                reimported_df = pd.read_csv(test_file)
                import_time = time.time() - start_time
                
                # Validate data integrity
                data_integrity_passed = (
                    len(fixtures_df) == len(reimported_df) and
                    list(fixtures_df.columns) == list(reimported_df.columns)
                )
                
                export_results.append({
                    'export_type': 'fixtures',
                    'record_count': len(fixtures_df),
                    'export_time': export_time,
                    'import_time': import_time,
                    'data_integrity': data_integrity_passed,
                    'file_size_kb': os.path.getsize(test_file) / 1024 if os.path.exists(test_file) else 0
                })
                
                # Cleanup
                if os.path.exists(test_file):
                    os.remove(test_file)
        
        except Exception as e:
            export_results.append({
                'export_type': 'fixtures',
                'error': str(e),
                'data_integrity': False
            })
        
        successful_exports = sum(1 for r in export_results if r.get('data_integrity', False))
        
        self.reliability_results['data_export'] = {
            'export_tests': len(export_results),
            'successful_exports': successful_exports,
            'export_results': export_results
        }
        
        print(f"   ✓ Tested {len(export_results)} export operations")
        print(f"   ✓ Export success rate: {(successful_exports/len(export_results)):.1%}")
        
        self.assertGreater(successful_exports, 0, "No successful data exports")
    
    def test_error_handling_robustness(self):
        """Test error handling and recovery mechanisms"""
        print("\n🛡️  Testing error handling robustness...")
        
        error_scenarios = []
        
        # Test invalid URL handling
        try:
            original_base_url = self.live_scraper.base_url
            self.live_scraper.base_url = "https://invalid-sofascore-url.com/api/v1"
            
            result = self.live_scraper.get_live_matches()
            
            # Should handle gracefully and return empty list
            error_scenarios.append({
                'scenario': 'invalid_api_url',
                'handled_gracefully': isinstance(result, list) and len(result) == 0,
                'error': None
            })
            
            # Restore original URL
            self.live_scraper.base_url = original_base_url
            
        except Exception as e:
            error_scenarios.append({
                'scenario': 'invalid_api_url',
                'handled_gracefully': False,
                'error': str(e)
            })
        
        # Test invalid date handling
        try:
            result = self.fixture_scraper.get_fixtures_by_date("invalid-date")
            error_scenarios.append({
                'scenario': 'invalid_date',
                'handled_gracefully': isinstance(result, list),
                'error': None
            })
        except Exception as e:
            error_scenarios.append({
                'scenario': 'invalid_date',
                'handled_gracefully': False,
                'error': str(e)
            })
        
        graceful_handling_count = sum(1 for s in error_scenarios if s['handled_gracefully'])
        
        self.reliability_results['error_handling'] = {
            'error_scenarios_tested': len(error_scenarios),
            'gracefully_handled': graceful_handling_count,
            'robustness_score': (graceful_handling_count / len(error_scenarios)) * 100,
            'scenarios': error_scenarios
        }
        
        print(f"   ✓ Tested {len(error_scenarios)} error scenarios")
        print(f"   ✓ Robustness score: {(graceful_handling_count / len(error_scenarios)) * 100:.1f}%")
        
        self.assertGreaterEqual(graceful_handling_count / len(error_scenarios), 0.8, 
                               "Error handling robustness too low")
    
    @classmethod
    def tearDownClass(cls):
        """Generate reliability report"""
        cls._generate_reliability_report()
    
    @classmethod
    def _generate_reliability_report(cls):
        """Generate comprehensive reliability report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/reports/reliability_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Pipeline Reliability Test Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for test_name, results in cls.reliability_results.items():
                f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                
                if isinstance(results, dict):
                    for key, value in results.items():
                        if key not in ['errors', 'scenarios', 'export_results']:
                            f.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                
                f.write("\n")
        
        print(f"\n📄 Reliability report saved: {report_file}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
EOF

# Create performance testing framework
echo "⚡ Creating performance testing framework..."
cat > tests/performance/test_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Performance testing for SofaScore pipeline
Tests response times, memory usage, and throughput
"""

import sys
import os
import unittest
import time
import psutil
import threading
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.live_scraper import LiveMatchScraper
from src.fixture_scraper import FixtureScraper
from config.database import engine
from tests.test_config import PERFORMANCE_TEST_CONFIG, VALIDATION_THRESHOLDS
from sqlalchemy import text

class PerformanceTester(unittest.TestCase):
    """Comprehensive performance testing suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up performance test environment"""
        cls.live_scraper = LiveMatchScraper()
        cls.fixture_scraper = FixtureScraper()
        cls.performance_results = {}
        cls.process = psutil.Process()
    
    def test_api_response_times(self):
        """Test API response time performance"""
        print("\n⚡ Testing API response times...")
        
        response_times = []
        memory_usage = []
        
        for i in range(5):  # Test 5 API calls
            # Monitor memory before call
            memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            
            try:
                fixtures = self.fixture_scraper.get_fixtures_by_date(
                    datetime.now().strftime('%Y-%m-%d')
                )
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Monitor memory after call
                memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
                memory_usage.append(memory_after - memory_before)
                
            except Exception as e:
                response_times.append(float('inf'))
                memory_usage.append(0)
            
            time.sleep(1)  # Rate limiting
        
        # Filter out failed requests
        valid_times = [t for t in response_times if t != float('inf')]
        
        self.performance_results['api_response_times'] = {
            'total_requests': len(response_times),
            'successful_requests': len(valid_times),
            'average_response_time': sum(valid_times) / len(valid_times) if valid_times else 0,
            'max_response_time': max(valid_times) if valid_times else 0,
            'min_response_time': min(valid_times) if valid_times else 0,
            'average_memory_delta': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            'response_times': valid_times
        }
        
        avg_time = self.performance_results['api_response_times']['average_response_time']
        max_time = VALIDATION_THRESHOLDS['max_api_response_time_seconds']
        
        print(f"   ✓ {len(valid_times)}/{len(response_times)} successful requests")
        print(f"   ✓ Average response time: {avg_time:.2f}s")
        print(f"   ✓ Max response time: {max(valid_times) if valid_times else 0:.2f}s")
        
        self.assertLess(avg_time, max_time, f"Average response time too slow: {avg_time:.2f}s")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        print("\n🗄️  Testing database query performance...")
        
        query_times = {}
        
        try:
            with engine.connect() as conn:
                # Test complex goal analysis query
                start_time = time.time()
                result = conn.execute(text("""
                    SELECT 
                        g.time_interval,
                        COUNT(*) as goal_count,
                        AVG(g.total_minute) as avg_minute,
                        COUNT(*) FILTER (WHERE g.is_late_goal = true) as late_goals,
                        m.competition
                    FROM goal_events g
                    JOIN live_matches m ON g.match_id = m.match_id
                    GROUP BY g.time_interval, m.competition
                    ORDER BY goal_count DESC
                """))
                query_times['complex_goal_analysis'] = time.time() - start_time
                result.fetchall()  # Consume results
                
                # Test simple count query
                start_time = time.time()
                result = conn.execute(text("SELECT COUNT(*) FROM live_matches"))
                query_times['simple_count'] = time.time() - start_time
                result.fetchall()
                
                # Test join query with statistics
                start_time = time.time()
                result = conn.execute(text("""
                    SELECT m.match_id, m.home_team, m.away_team, 
                           COUNT(g.goal_id) as total_goals
                    FROM live_matches m
                    LEFT JOIN goal_events g ON m.match_id = g.match_id
                    GROUP BY m.match_id, m.home_team, m.away_team
                    ORDER BY total_goals DESC
                    LIMIT 20
                """))
                query_times['join_with_aggregation'] = time.time() - start_time
                result.fetchall()
        
        except Exception as e:
            query_times['error'] = str(e)
        
        max_query_time = VALIDATION_THRESHOLDS['database_query_timeout_seconds']
        slow_queries = {k: v for k, v in query_times.items() if v > max_query_time}
        
        self.performance_results['database_query_performance'] = {
            'queries_tested': len([k for k in query_times.keys() if k != 'error']),
            'query_times': query_times,
            'average_query_time': sum(v for v in query_times.values() if isinstance(v, (int, float))) / len([v for v in query_times.values() if isinstance(v, (int, float))]) if query_times else 0,
            'slow_queries': slow_queries,
            'max_query_time': max(v for v in query_times.values() if isinstance(v, (int, float))) if query_times else 0
        }
        
        print(f"   ✓ Tested {len([k for k in query_times.keys() if k != 'error'])} database queries")
        for query_name, query_time in query_times.items():
            if isinstance(query_time, (int, float)):
                print(f"   ✓ {query_name}: {query_time:.3f}s")
        
        self.assertEmpty(slow_queries, f"Slow queries detected: {slow_queries}")
    
    def assertEmpty(self, container, msg=None):
        """Assert that container is empty"""
        self.assertEqual(len(container), 0, msg)
    
    def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        print("\n🧠 Testing memory usage under load...")
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        peak_memory = initial_memory
        memory_samples = [initial_memory]
        
        def monitor_memory():
            """Monitor memory usage in background"""
            nonlocal peak_memory
            for _ in range(30):  # Monitor for 30 seconds
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                peak_memory = max(peak_memory, current_memory)
                time.sleep(1)
        
        # Start memory monitoring
        monitor_thread = threading.Thread(target=monitor_memory)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Perform intensive operations
        try:
            for i in range(3):
                # Scrape fixtures multiple times
                fixtures = self.fixture_scraper.get_upcoming_fixtures(days_ahead=5)
                
                if fixtures:
                    # Convert to DataFrame (memory intensive)
                    df = self.fixture_scraper.to_dataframe(fixtures)
                    
                    # Perform some DataFrame operations
                    if not df.empty:
                        _ = df.groupby('tournament').size()
                        _ = df.sort_values('kickoff_date') if 'kickoff_date' in df.columns else df
                
                time.sleep(2)
        
        except Exception as e:
            print(f"   ⚠️  Error during memory test: {e}")
        
        # Wait for monitoring to complete
        monitor_thread.join(timeout=5)
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        max_allowed_memory = PERFORMANCE_TEST_CONFIG['max_memory_usage_mb']
        
        self.performance_results['memory_usage'] = {
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': peak_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': memory_growth,
            'memory_samples': len(memory_samples),
            'average_memory_mb': sum(memory_samples) / len(memory_samples),
            'within_limits': peak_memory < max_allowed_memory
        }
        
        print(f"   ✓ Initial memory: {initial_memory:.1f} MB")
        print(f"   ✓ Peak memory: {peak_memory:.1f} MB")
        print(f"   ✓ Memory growth: {memory_growth:.1f} MB")
        
        self.assertLess(peak_memory, max_allowed_memory, 
                       f"Peak memory usage too high: {peak_memory:.1f} MB")
    
    def test_data_processing_throughput(self):
        """Test data processing throughput"""
        print("\n📈 Testing data processing throughput...")
        
        throughput_metrics = {}
        
        try:
            # Test fixture processing throughput
            start_time = time.time()
            fixtures = self.fixture_scraper.get_upcoming_fixtures(days_ahead=7)
            fetch_time = time.time() - start_time
            
            if fixtures:
                start_time = time.time()
                fixtures_df = self.fixture_scraper.to_dataframe(fixtures)
                processing_time = time.time() - start_time
                
                throughput_metrics['fixture_processing'] = {
                    'records_processed': len(fixtures),
                    'fetch_time': fetch_time,
                    'processing_time': processing_time,
                    'total_time': fetch_time + processing_time,
                    'records_per_second': len(fixtures) / (fetch_time + processing_time) if (fetch_time + processing_time) > 0 else 0
                }
        
        except Exception as e:
            throughput_metrics['fixture_processing'] = {'error': str(e)}
        
        # Test CSV export throughput
        try:
            if fixtures:
                test_file = "tests/fixtures/sample_data/throughput_test.csv"
                
                start_time = time.time()
                fixtures_df.to_csv(test_file, index=False)
                export_time = time.time() - start_time
                
                file_size = os.path.getsize(test_file) / 1024  # KB
                
                throughput_metrics['csv_export'] = {
                    'records_exported': len(fixtures_df),
                    'export_time': export_time,
                    'file_size_kb': file_size,
                    'records_per_second': len(fixtures_df) / export_time if export_time > 0 else 0,
                    'kb_per_second': file_size / export_time if export_time > 0 else 0
                }
                
                # Cleanup
                if os.path.exists(test_file):
                    os.remove(test_file)
        
        except Exception as e:
            throughput_metrics['csv_export'] = {'error': str(e)}
        
        self.performance_results['data_processing_throughput'] = throughput_metrics
        
        for process_type, metrics in throughput_metrics.items():
            if 'error' not in metrics:
                records_per_sec = metrics.get('records_per_second', 0)
                print(f"   ✓ {process_type}: {records_per_sec:.1f} records/second")
        
        # Basic throughput assertion (should process at least 10 records per second)
        for process_type, metrics in throughput_metrics.items():
            if 'error' not in metrics and 'records_per_second' in metrics:
                self.assertGreater(metrics['records_per_second'], 10, 
                                 f"{process_type} throughput too low")
    
    @classmethod
    def tearDownClass(cls):
        """Generate performance report"""
        cls._generate_performance_report()
    
    @classmethod
    def _generate_performance_report(cls):
        """Generate comprehensive performance report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/reports/performance_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Pipeline Performance Test Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # System info
            f.write("## System Information\n\n")
            f.write(f"- **CPU Count**: {psutil.cpu_count()}\n")
            f.write(f"- **Memory Total**: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB\n")
            f.write(f"- **Python Version**: {sys.version.split()[0]}\n\n")
            
            # Performance results
            for test_name, results in cls.performance_results.items():
                f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                
                if isinstance(results, dict):
                    for key, value in results.items():
                        if key not in ['response_times', 'memory_samples', 'query_times']:
                            f.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                
                f.write("\n")
        
        print(f"\n📄 Performance report saved: {report_file}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
EOF

# Create data quality monitoring
echo "📋 Creating data quality monitoring..."
cat > tests/data_quality/test_data_quality.py << 'EOF'
#!/usr/bin/env python3
"""
Data Quality Monitoring for SofaScore pipeline
Comprehensive data quality checks and metrics
"""

import sys
import os
import unittest
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.database import engine
from tests.test_config import VALIDATION_THRESHOLDS
from sqlalchemy import text

class DataQualityMonitor(unittest.TestCase):
    """Comprehensive data quality monitoring suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up data quality monitoring"""
        cls.quality_metrics = {}
        cls.data_issues = []
    
    def test_data_freshness(self):
        """Test data freshness and update frequency"""
        print("\n🕐 Testing data freshness...")
        
        freshness_metrics = {}
        
        try:
            with engine.connect() as conn:
                # Check last update times for each table
                tables = ['live_matches', 'goal_events', 'team_statistics', 'fixtures']
                
                for table in tables:
                    result = conn.execute(text(f"""
                        SELECT 
                            COUNT(*) as total_records,
                            MAX(scraped_at) as last_update,
                            COUNT(*) FILTER (WHERE scraped_at > NOW() - INTERVAL '24 hours') as recent_records
                        FROM {table}
                        WHERE scraped_at IS NOT NULL
                    """))
                    
                    row = result.fetchone()
                    if row:
                        last_update = row[1]
                        hours_since_update = None
                        
                        if last_update:
                            hours_since_update = (datetime.now() - last_update).total_seconds() / 3600
                        
                        freshness_metrics[table] = {
                            'total_records': row[0],
                            'last_update': last_update.isoformat() if last_update else None,
                            'hours_since_update': hours_since_update,
                            'recent_records': row[2],
                            'is_fresh': hours_since_update < 24 if hours_since_update else False
                        }
        
        except Exception as e:
            self.data_issues.append(f"Data freshness check failed: {e}")
        
        self.quality_metrics['data_freshness'] = freshness_metrics
        
        # Report freshness
        for table, metrics in freshness_metrics.items():
            hours_since = metrics.get('hours_since_update', float('inf'))
            recent_count = metrics.get('recent_records', 0)
            
            print(f"   ✓ {table}: {recent_count} recent records")
            if hours_since is not None and hours_since != float('inf'):
                print(f"     Last update: {hours_since:.1f} hours ago")
        
        # Assert reasonable freshness for active tables
        active_tables = ['live_matches', 'fixtures']
        for table in active_tables:
            if table in freshness_metrics:
                hours_since = freshness_metrics[table].get('hours_since_update', float('inf'))
                if hours_since != float('inf'):
                    self.assertLess(hours_since, 48, f"{table} data too stale: {hours_since:.1f} hours")
    
    def test_data_consistency(self):
        """Test data consistency across related tables"""
        print("\n🔗 Testing data consistency...")
        
        consistency_issues = []
        
        try:
            with engine.connect() as conn:
                # Check for orphaned goal events
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM goal_events g
                    LEFT JOIN live_matches m ON g.match_id = m.match_id
                    WHERE m.match_id IS NULL
                """))
                orphaned_goals = result.scalar()
                
                if orphaned_goals > 0:
                    consistency_issues.append(f"{orphaned_goals} orphaned goal events")
                
                # Check for matches without basic info
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM live_matches
                    WHERE home_team IS NULL OR away_team IS NULL
                """))
                incomplete_matches = result.scalar()
                
                if incomplete_matches > 0:
                    consistency_issues.append(f"{incomplete_matches} matches missing team names")
                
                # Check for impossible goal timing
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM goal_events
                    WHERE total_minute < 0 OR total_minute > 120
                """))
                impossible_goals = result.scalar()
                
                if impossible_goals > 0:
                    consistency_issues.append(f"{impossible_goals} goals with impossible timing")
                
                # Check for future fixtures in the past
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM fixtures
                    WHERE kickoff_date < CURRENT_DATE - INTERVAL '1 day'
                    AND status NOT IN ('finished', 'postponed', 'cancelled')
                """))
                stale_fixtures = result.scalar()
                
                if stale_fixtures > 0:
                    consistency_issues.append(f"{stale_fixtures} stale fixtures")
        
        except Exception as e:
            consistency_issues.append(f"Consistency check error: {e}")
        
        self.quality_metrics['data_consistency'] = {
            'issues_found': len(consistency_issues),
            'issues': consistency_issues,
            'consistency_score': max(0, 100 - len(consistency_issues) * 10)  # Deduct 10 points per issue
        }
        
        print(f"   ✓ Found {len(consistency_issues)} consistency issues")
        for issue in consistency_issues:
            print(f"     ⚠️  {issue}")
        
        self.assertLess(len(consistency_issues), 5, f"Too many consistency issues: {consistency_issues}")
    
    def test_data_completeness_detailed(self):
        """Test detailed data completeness across all fields"""
        print("\n📊 Testing detailed data completeness...")
        
        completeness_metrics = {}
        
        try:
            with engine.connect() as conn:
                # Goal events completeness
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(exact_timestamp) as has_timestamp,
                        COUNT(scoring_player) as has_player,
                        COUNT(team_side) as has_team_side,
                        COUNT(goal_type) as has_goal_type,
                        COUNT(competition) as has_competition
                    FROM goal_events
                """))
                
                row = result.fetchone()
                if row and row[0] > 0:
                    total = row[0]
                    completeness_metrics['goal_events'] = {
                        'timestamp_completeness': (row[1] / total) * 100,
                        'player_completeness': (row[2] / total) * 100,
                        'team_side_completeness': (row[3] / total) * 100,
                        'goal_type_completeness': (row[4] / total) * 100,
                        'competition_completeness': (row[5] / total) * 100,
                        'overall_completeness': ((row[1] + row[2] + row[3] + row[4] + row[5]) / (total * 5)) * 100
                    }
                
                # Team statistics completeness
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(possession_percentage) as has_possession,
                        COUNT(shots_on_target) as has_shots_on_target,
                        COUNT(total_shots) as has_total_shots,
                        COUNT(corners) as has_corners,
                        COUNT(fouls) as has_fouls
                    FROM team_statistics
                """))
                
                row = result.fetchone()
                if row and row[0] > 0:
                    total = row[0]
                    completeness_metrics['team_statistics'] = {
                        'possession_completeness': (row[1] / total) * 100,
                        'shots_on_target_completeness': (row[2] / total) * 100,
                        'total_shots_completeness': (row[3] / total) * 100,
                        'corners_completeness': (row[4] / total) * 100,
                        'fouls_completeness': (row[5] / total) * 100,
                        'overall_completeness': ((row[1] + row[2] + row[3] + row[4] + row[5]) / (total * 5)) * 100
                    }
                
                # Fixtures completeness
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(kickoff_time) as has_kickoff_time,
                        COUNT(tournament) as has_tournament,
                        COUNT(venue) as has_venue,
                        COUNT(status) as has_status
                    FROM fixtures
                """))
                
                row = result.fetchone()
                if row and row[0] > 0:
                    total = row[0]
                    completeness_metrics['fixtures'] = {
                        'kickoff_time_completeness': (row[1] / total) * 100,
                        'tournament_completeness': (row[2] / total) * 100,
                        'venue_completeness': (row[3] / total) * 100,
                        'status_completeness': (row[4] / total) * 100,
                        'overall_completeness': ((row[1] + row[2] + row[3] + row[4]) / (total * 4)) * 100
                    }
        
        except Exception as e:
            self.data_issues.append(f"Completeness check failed: {e}")
        
        self.quality_metrics['detailed_completeness'] = completeness_metrics
        
        # Report completeness
        min_completeness = VALIDATION_THRESHOLDS['minimum_data_completeness'] * 100
        
        for table, metrics in completeness_metrics.items():
            overall = metrics.get('overall_completeness', 0)
            print(f"   ✓ {table}: {overall:.1f}% overall completeness")
            
            for field, completeness in metrics.items():
                if field != 'overall_completeness':
                    status = "✓" if completeness >= min_completeness else "⚠️"
                    print(f"     {status} {field}: {completeness:.1f}%")
    
    def test_data_distribution_analysis(self):
        """Test data distribution and identify anomalies"""
        print("\n📈 Testing data distribution analysis...")
        
        distribution_metrics = {}
        
        try:
            with engine.connect() as conn:
                # Goal timing distribution
                result = conn.execute(text("""
                    SELECT 
                        time_interval,
                        COUNT(*) as goal_count,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
                    FROM goal_events
                    WHERE time_interval IS NOT NULL
                    GROUP BY time_interval
                    ORDER BY 
                        CASE time_interval
                            WHEN '0-15' THEN 1
                            WHEN '16-30' THEN 2
                            WHEN '31-45' THEN 3
                            WHEN '46-60' THEN 4
                            WHEN '61-75' THEN 5
                            WHEN '76-90' THEN 6
                            WHEN '90+' THEN 7
                        END
                """))
                
                goal_distribution = {}
                for row in result:
                    goal_distribution[row[0]] = {
                        'count': row[1],
                        'percentage': float(row[2])
                    }
                
                distribution_metrics['goal_timing'] = goal_distribution
                
                # Competition distribution
                result = conn.execute(text("""
                    SELECT 
                        competition,
                        COUNT(DISTINCT match_id) as match_count,
                        COUNT(*) as goal_count
                    FROM goal_events
                    WHERE competition IS NOT NULL
                    GROUP BY competition
                    ORDER BY goal_count DESC
                    LIMIT 10
                """))
                
                competition_distribution = {}
                for row in result:
                    competition_distribution[row[0]] = {
                        'matches': row[1],
                        'goals': row[2],
                        'goals_per_match': row[2] / row[1] if row[1] > 0 else 0
                    }
                
                distribution_metrics['competition_goals'] = competition_distribution
        
        except Exception as e:
            self.data_issues.append(f"Distribution analysis failed: {e}")
        
        self.quality_metrics['data_distribution'] = distribution_metrics
        
        # Report distributions
        if 'goal_timing' in distribution_metrics:
            print("   Goal timing distribution:")
            for interval, data in distribution_metrics['goal_timing'].items():
                print(f"     {interval}: {data['count']} goals ({data['percentage']}%)")
        
        if 'competition_goals' in distribution_metrics:
            print("   Top competitions by goals:")
            for comp, data in list(distribution_metrics['competition_goals'].items())[:5]:
                print(f"     {comp}: {data['goals']} goals in {data['matches']} matches")
    
    def test_data_quality_score(self):
        """Calculate overall data quality score"""
        print("\n🎯 Calculating overall data quality score...")
        
        scores = {}
        
        # Freshness score (0-25 points)
        freshness_metrics = self.quality_metrics.get('data_freshness', {})
        fresh_tables = sum(1 for table_metrics in freshness_metrics.values() 
                          if isinstance(table_metrics, dict) and table_metrics.get('is_fresh', False))
        total_tables = len(freshness_metrics)
        freshness_score = (fresh_tables / total_tables * 25) if total_tables > 0 else 0
        scores['freshness'] = freshness_score
        
        # Consistency score (0-25 points)
        consistency_metrics = self.quality_metrics.get('data_consistency', {})
        consistency_score = min(25, consistency_metrics.get('consistency_score', 0) / 4)
        scores['consistency'] = consistency_score
        
        # Completeness score (0-25 points)
        completeness_metrics = self.quality_metrics.get('detailed_completeness', {})
        total_completeness = 0
        completeness_count = 0
        
        for table_metrics in completeness_metrics.values():
            if isinstance(table_metrics, dict) and 'overall_completeness' in table_metrics:
                total_completeness += table_metrics['overall_completeness']
                completeness_count += 1
        
        avg_completeness = total_completeness / completeness_count if completeness_count > 0 else 0
        completeness_score = (avg_completeness / 100) * 25
        scores['completeness'] = completeness_score
        
        # Distribution score (0-25 points)
        distribution_metrics = self.quality_metrics.get('data_distribution', {})
        distribution_score = 25 if distribution_metrics else 0  # Basic check for presence
        scores['distribution'] = distribution_score
        
        # Calculate overall score
        overall_score = sum(scores.values())
        
        self.quality_metrics['overall_quality_score'] = {
            'scores': scores,
            'overall_score': overall_score,
            'grade': self._get_quality_grade(overall_score)
        }
        
        print(f"   Data Quality Scores:")
        for category, score in scores.items():
            print(f"     {category.title()}: {score:.1f}/25")
        
        print(f"   Overall Quality Score: {overall_score:.1f}/100 ({self._get_quality_grade(overall_score)})")
        
        # Assert minimum quality score
        self.assertGreaterEqual(overall_score, 60, f"Data quality score too low: {overall_score:.1f}/100")
    
    def _get_quality_grade(self, score):
        """Get quality grade based on score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    @classmethod
    def tearDownClass(cls):
        """Generate data quality report"""
        cls._generate_quality_report()
    
    @classmethod
    def _generate_quality_report(cls):
        """Generate comprehensive data quality report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/reports/data_quality_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Data Quality Assessment Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            overall_metrics = cls.quality_metrics.get('overall_quality_score', {})
            if overall_metrics:
                f.write("## Executive Summary\n\n")
                f.write(f"**Overall Quality Score: {overall_metrics.get('overall_score', 0):.1f}/100 (Grade: {overall_metrics.get('grade', 'N/A')})**\n\n")
            
            # Detailed metrics
            for test_name, results in cls.quality_metrics.items():
                if test_name != 'overall_quality_score':
                    f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                    
                    if isinstance(results, dict):
                        cls._write_metrics_to_report(f, results, level=0)
                    
                    f.write("\n")
            
            # Issues found
            if cls.data_issues:
                f.write("## Issues Identified\n\n")
                for issue in cls.data_issues:
                    f.write(f"- {issue}\n")
                f.write("\n")
        
        print(f"\n📄 Data quality report saved: {report_file}")
    
    @classmethod
    def _write_metrics_to_report(cls, file, metrics, level=0):
        """Recursively write metrics to report file"""
        indent = "  " * level
        
        for key, value in metrics.items():
            if isinstance(value, dict):
                file.write(f"{indent}- **{key.replace('_', ' ').title()}**:\n")
                cls._write_metrics_to_report(file, value, level + 1)
            elif isinstance(value, list):
                file.write(f"{indent}- **{key.replace('_', ' ').title()}**: {len(value)} items\n")
                if len(value) <= 5:  # Show small lists
                    for item in value:
                        file.write(f"{indent}  - {item}\n")
            else:
                file.write(f"{indent}- **{key.replace('_', ' ').title()}**: {value}\n")

if __name__ == "__main__":
    unittest.main(verbosity=2)
EOF

# Create integration tests
echo "🔧 Creating integration tests..."
cat > tests/integration/test_end_to_end.py << 'EOF'
#!/usr/bin/env python3
"""
End-to-end integration tests for SofaScore pipeline
Tests complete workflow from data collection to database storage
"""

import sys
import os
import unittest
import tempfile
import shutil
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.main import main as run_pipeline
from database.csv_import import CSVImporter
from database.db_manager import DatabaseManager
from config.database import engine
from sqlalchemy import text

class EndToEndIntegrationTest(unittest.TestCase):
    """End-to-end pipeline integration tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test environment"""
        cls.test_export_dir = tempfile.mkdtemp(prefix="sofascore_test_")
        cls.integration_results = {}
        
    @classmethod
    def tearDownClass(cls):
        """Clean up integration test environment"""
        if os.path.exists(cls.test_export_dir):
            shutil.rmtree(cls.test_export_dir)
    
    def test_complete_pipeline_workflow(self):
        """Test complete pipeline from data collection to storage"""
        print("\n🚀 Testing complete pipeline workflow...")
        
        workflow_results = {}
        
        # Step 1: Test data collection
        print("   Step 1: Data collection...")
        try:
            # Note: In a real test, we'd mock the API calls
            # For now, we'll test the components independently
            
            from src.fixture_scraper import FixtureScraper
            fixture_scraper = FixtureScraper()
            
            # Test fixture collection
            fixtures = fixture_scraper.get_upcoming_fixtures(days_ahead=2)
            workflow_results['data_collection'] = {
                'fixtures_collected': len(fixtures),
                'success': len(fixtures) >= 0  # Allow zero fixtures
            }
            
            print(f"     ✓ Collected {len(fixtures)} fixtures")
            
        except Exception as e:
            workflow_results['data_collection'] = {
                'success': False,
                'error': str(e)
            }
            print(f"     ❌ Data collection failed: {e}")
        
        # Step 2: Test CSV export
        print("   Step 2: CSV export...")
        try:
            if fixtures:
                fixtures_df = fixture_scraper.to_dataframe(fixtures)
                test_csv = os.path.join(self.test_export_dir, "test_fixtures.csv")
                fixtures_df.to_csv(test_csv, index=False)
                
                # Verify file exists and has content
                file_exists = os.path.exists(test_csv)
                file_size = os.path.getsize(test_csv) if file_exists else 0
                
                workflow_results['csv_export'] = {
                    'file_created': file_exists,
                    'file_size_bytes': file_size,
                    'records_exported': len(fixtures_df),
                    'success': file_exists and file_size > 0
                }
                
                print(f"     ✓ Exported {len(fixtures_df)} records to CSV")
            else:
                workflow_results['csv_export'] = {
                    'success': True,
                    'message': 'No data to export'
                }
                print("     ✓ No data to export (valid result)")
                
        except Exception as e:
            workflow_results['csv_export'] = {
                'success': False,
                'error': str(e)
            }
            print(f"     ❌ CSV export failed: {e}")
        
        # Step 3: Test database operations
        print("   Step 3: Database operations...")
        try:
            db_manager = DatabaseManager()
            
            # Test database connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                connection_success = result.scalar() == 1
            
            # Test basic queries
            fixture_count = db_manager.get_table_count('fixtures')
            match_count = db_manager.get_table_count('live_matches')
            goal_count = db_manager.get_table_count('goal_events')
            
            workflow_results['database_operations'] = {
                'connection_success': connection_success,
                'fixture_count': fixture_count,
                'match_count': match_count,
                'goal_count': goal_count,
                'success': connection_success
            }
            
            print(f"     ✓ Database connection successful")
            print(f"     ✓ Current data: {fixture_count} fixtures, {match_count} matches, {goal_count} goals")
            
        except Exception as e:
            workflow_results['database_operations'] = {
                'success': False,
                'error': str(e)
            }
            print(f"     ❌ Database operations failed: {e}")
        
        self.integration_results['complete_workflow'] = workflow_results
        
        # Assert overall workflow success
        critical_steps = ['data_collection', 'database_operations']
        failed_steps = [step for step in critical_steps 
                       if not workflow_results.get(step, {}).get('success', False)]
        
        self.assertEqual(len(failed_steps), 0, f"Critical workflow steps failed: {failed_steps}")
    
    def test_data_consistency_across_pipeline(self):
        """Test data consistency from collection through storage"""
        print("\n🔗 Testing data consistency across pipeline...")
        
        consistency_results = {}
        
        try:
            with engine.connect() as conn:
                # Test referential integrity
                result = conn.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM goal_events) as total_goals,
                        (SELECT COUNT(*) FROM goal_events g 
                         JOIN live_matches m ON g.match_id = m.match_id) as goals_with_matches,
                        (SELECT COUNT(*) FROM team_statistics) as total_team_stats,
                        (SELECT COUNT(*) FROM team_statistics ts 
                         JOIN live_matches m ON ts.match_id = m.match_id) as stats_with_matches
                """))
                
                row = result.fetchone()
                total_goals, goals_with_matches = row[0], row[1]
                total_team_stats, stats_with_matches = row[2], row[3]
                
                # Calculate integrity ratios
                goal_integrity = (goals_with_matches / total_goals * 100) if total_goals > 0 else 100
                stats_integrity = (stats_with_matches / total_team_stats * 100) if total_team_stats > 0 else 100
                
                consistency_results = {
                    'total_goals': total_goals,
                    'goals_with_matches': goals_with_matches,
                    'goal_integrity_percentage': goal_integrity,
                    'total_team_stats': total_team_stats,
                    'stats_with_matches': stats_with_matches,
                    'stats_integrity_percentage': stats_integrity,
                    'overall_integrity': (goal_integrity + stats_integrity) / 2
                }
                
                print(f"     ✓ Goal events integrity: {goal_integrity:.1f}%")
                print(f"     ✓ Team stats integrity: {stats_integrity:.1f}%")
                print(f"     ✓ Overall integrity: {consistency_results['overall_integrity']:.1f}%")
                
        except Exception as e:
            consistency_results = {
                'error': str(e),
                'overall_integrity': 0
            }
            print(f"     ❌ Consistency check failed: {e}")
        
        self.integration_results['data_consistency'] = consistency_results
        
        # Assert high data integrity
        if 'overall_integrity' in consistency_results:
            self.assertGreaterEqual(consistency_results['overall_integrity'], 90, 
                                   "Data integrity across pipeline too low")
    
    def test_error_recovery_workflow(self):
        """Test pipeline error recovery and resilience"""
        print("\n🛡️  Testing error recovery workflow...")
        
        recovery_results = {}
        
        # Test graceful handling of API failures
        try:
            from src.live_scraper import LiveMatchScraper
            live_scraper = LiveMatchScraper()
            
            # Test with invalid base URL (simulating API failure)
            original_url = live_scraper.base_url
            live_scraper.base_url = "https://invalid-api-endpoint.com/api/v1"
            
            # Should not crash, should return empty list
            result = live_scraper.get_live_matches()
            
            api_failure_handled = isinstance(result, list)
            
            # Restore original URL
            live_scraper.base_url = original_url
            
            recovery_results['api_failure_handling'] = {
                'handled_gracefully': api_failure_handled,
                'returned_empty_list': len(result) == 0
            }
            
            print(f"     ✓ API failure handled gracefully: {api_failure_handled}")
            
        except Exception as e:
            recovery_results['api_failure_handling'] = {
                'handled_gracefully': False,
                'error': str(e)
            }
            print(f"     ❌ API failure handling failed: {e}")
        
        # Test database connection recovery
        try:
            from config.database import test_connection
            
            # Test connection
            connection_works = test_connection()
            
            recovery_results['database_recovery'] = {
                'connection_successful': connection_works
            }
            
            print(f"     ✓ Database connection recovery: {connection_works}")
            
        except Exception as e:
            recovery_results['database_recovery'] = {
                'connection_successful': False,
                'error': str(e)
            }
        
        self.integration_results['error_recovery'] = recovery_results
        
        # Assert error recovery works
        api_handled = recovery_results.get('api_failure_handling', {}).get('handled_gracefully', False)
        db_works = recovery_results.get('database_recovery', {}).get('connection_successful', False)
        
        self.assertTrue(api_handled, "API failure not handled gracefully")
        self.assertTrue(db_works, "Database connection recovery failed")
    
    def test_performance_under_load(self):
        """Test pipeline performance under simulated load"""
        print("\n⚡ Testing performance under load...")
        
        performance_results = {}
        
        try:
            import time
            from src.fixture_scraper import FixtureScraper
            
            fixture_scraper = FixtureScraper()
            
            # Test multiple rapid requests
            start_time = time.time()
            request_times = []
            
            for i in range(3):  # Limited for CI/CD
                request_start = time.time()
                fixtures = fixture_scraper.get_fixtures_by_date(
                    datetime.now().strftime('%Y-%m-%d')
                )
                request_end = time.time()
                
                request_times.append(request_end - request_start)
                time.sleep(1)  # Rate limiting
            
            total_time = time.time() - start_time
            avg_request_time = sum(request_times) / len(request_times)
            
            performance_results = {
                'total_requests': len(request_times),
                'total_time': total_time,
                'average_request_time': avg_request_time,
                'max_request_time': max(request_times),
                'performance_acceptable': avg_request_time < 10  # 10 second threshold
            }
            
            print(f"     ✓ {len(request_times)} requests in {total_time:.2f}s")
            print(f"     ✓ Average request time: {avg_request_time:.2f}s")
            
        except Exception as e:
            performance_results = {
                'error': str(e),
                'performance_acceptable': False
            }
            print(f"     ❌ Performance test failed: {e}")
        
        self.integration_results['performance_under_load'] = performance_results
        
        # Assert acceptable performance
        if 'performance_acceptable' in performance_results:
            self.assertTrue(performance_results['performance_acceptable'], 
                          "Performance under load not acceptable")
    
    def tearDown(self):
        """Clean up after each test"""
        pass

if __name__ == "__main__":
    unittest.main(verbosity=2)
EOF

# Create test runner script
echo "🏃 Creating test runner script..."
cat > tests/run_all_tests.py << 'EOF'
#!/usr/bin/env python3
"""
Comprehensive test runner for SofaScore pipeline Stage 4 validation
Runs all test suites and generates combined report
"""

import sys
import os
import unittest
import time
from datetime import datetime
import subprocess

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_suite(test_module, suite_name):
    """Run a specific test suite and capture results"""
    print(f"\n{'='*60}")
    print(f"RUNNING {suite_name.upper()}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Import and run the test module
        suite = unittest.TestLoader().loadTestsFromModule(test_module)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'suite_name': suite_name,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'duration': duration,
            'status': 'PASSED' if len(result.failures) == 0 and len(result.errors) == 0 else 'FAILED'
        }
        
    except Exception as e:
        return {
            'suite_name': suite_name,
            'tests_run': 0,
            'failures': 1,
            'errors': 0,
            'success_rate': 0,
            'duration': time.time() - start_time,
            'status': 'ERROR',
            'error': str(e)
        }

def main():
    """Run all Stage 4 validation tests"""
    print("SofaScore Pipeline - Stage 4: Comprehensive Validation")
    print("=" * 70)
    print(f"Test execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Import test modules
    test_modules = []
    suite_results = []
    
    try:
        from tests.validation.test_data_accuracy import DataAccuracyValidator
        test_modules.append((DataAccuracyValidator, "Data Accuracy Validation"))
    except ImportError as e:
        print(f"⚠️  Could not import Data Accuracy tests: {e}")
    
    try:
        from tests.validation.test_reliability import ReliabilityTester
        test_modules.append((ReliabilityTester, "Reliability Testing"))
    except ImportError as e:
        print(f"⚠️  Could not import Reliability tests: {e}")
    
    try:
        from tests.performance.test_performance import PerformanceTester
        test_modules.append((PerformanceTester, "Performance Testing"))
    except ImportError as e:
        print(f"⚠️  Could not import Performance tests: {e}")
    
    try:
        from tests.data_quality.test_data_quality import DataQualityMonitor
        test_modules.append((DataQualityMonitor, "Data Quality Monitoring"))
    except ImportError as e:
        print(f"⚠️  Could not import Data Quality tests: {e}")
    
    try:
        from tests.integration.test_end_to_end import EndToEndIntegrationTest
        test_modules.append((EndToEndIntegrationTest, "End-to-End Integration"))
    except ImportError as e:
        print(f"⚠️  Could not import Integration tests: {e}")
    
    # Run all test suites
    overall_start = time.time()
    
    for test_module, suite_name in test_modules:
        try:
            # Create a module instance for testing
            import types
            module_instance = types.ModuleType(test_module.__name__)
            setattr(module_instance, test_module.__name__, test_module)
            
            result = run_test_suite(module_instance, suite_name)
            suite_results.append(result)
            
        except Exception as e:
            print(f"❌ Failed to run {suite_name}: {e}")
            suite_results.append({
                'suite_name': suite_name,
                'status': 'ERROR',
                'error': str(e)
            })
    
    overall_duration = time.time() - overall_start
    
    # Generate summary report
    generate_summary_report(suite_results, overall_duration)
    
    # Return exit code based on results
    failed_suites = [r for r in suite_results if r.get('status') != 'PASSED']
    return 1 if failed_suites else 0

def generate_summary_report(suite_results, total_duration):
    """Generate comprehensive summary report"""
    print(f"\n{'='*70}")
    print("STAGE 4 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    total_tests = sum(r.get('tests_run', 0) for r in suite_results)
    total_failures = sum(r.get('failures', 0) for r in suite_results)
    total_errors = sum(r.get('errors', 0) for r in suite_results)
    
    passed_suites = [r for r in suite_results if r.get('status') == 'PASSED']
    failed_suites = [r for r in suite_results if r.get('status') == 'FAILED']
    error_suites = [r for r in suite_results if r.get('status') == 'ERROR']
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total Test Suites: {len(suite_results)}")
    print(f"   Passed Suites: {len(passed_suites)}")
    print(f"   Failed Suites: {len(failed_suites)}")
    print(f"   Error Suites: {len(error_suites)}")
    print(f"   Total Tests Run: {total_tests}")
    print(f"   Total Duration: {total_duration:.1f} seconds")
    
    if total_tests > 0:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests) * 100
        print(f"   Overall Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 SUITE DETAILS:")
    for result in suite_results:
        status_icon = "✅" if result.get('status') == 'PASSED' else "❌"
        suite_name = result.get('suite_name', 'Unknown')
        duration = result.get('duration', 0)
        
        print(f"   {status_icon} {suite_name}: {result.get('status', 'UNKNOWN')} ({duration:.1f}s)")
        
        if result.get('tests_run', 0) > 0:
            success_rate = result.get('success_rate', 0)
            print(f"      Tests: {result.get('tests_run', 0)}, Success Rate: {success_rate:.1f}%")
        
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Save summary to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = f"tests/reports/stage4_validation_summary_{timestamp}.md"
    
    try:
        with open(summary_file, 'w') as f:
            f.write("# Stage 4 Validation Summary Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Test Suites**: {len(suite_results)}\n")
            f.write(f"- **Passed Suites**: {len(passed_suites)}\n")
            f.write(f"- **Failed Suites**: {len(failed_suites)}\n")
            f.write(f"- **Total Tests**: {total_tests}\n")
            f.write(f"- **Total Duration**: {total_duration:.1f} seconds\n")
            
            if total_tests > 0:
                success_rate = ((total_tests - total_failures - total_errors) / total_tests) * 100
                f.write(f"- **Overall Success Rate**: {success_rate:.1f}%\n")
            
            f.write("\n## Test Suite Results\n\n")
            
            for result in suite_results:
                f.write(f"### {result.get('suite_name', 'Unknown')}\n\n")
                f.write(f"- **Status**: {result.get('status', 'UNKNOWN')}\n")
                f.write(f"- **Duration**: {result.get('duration', 0):.1f} seconds\n")
                
                if result.get('tests_run', 0) > 0:
                    f.write(f"- **Tests Run**: {result.get('tests_run', 0)}\n")
                    f.write(f"- **Failures**: {result.get('failures', 0)}\n")
                    f.write(f"- **Errors**: {result.get('errors', 0)}\n")
                    f.write(f"- **Success Rate**: {result.get('success_rate', 0):.1f}%\n")
                
                if 'error' in result:
                    f.write(f"- **Error**: {result['error']}\n")
                
                f.write("\n")
        
        print(f"\n📄 Summary report saved: {summary_file}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save summary report: {e}")
    
    # Final status
    if len(failed_suites) == 0 and len(error_suites) == 0:
        print(f"\n🎉 STAGE 4 VALIDATION COMPLETED SUCCESSFULLY!")
        print(f"✅ All {len(suite_results)} test suites passed")
        print(f"🚀 Pipeline is ready for production deployment")
    else:
        print(f"\n❌ STAGE 4 VALIDATION FAILED")
        print(f"⚠️  {len(failed_suites)} failed suites, {len(error_suites)} error suites")
        print(f"🔧 Please review and fix issues before production deployment")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
EOF

# Create validation setup completion script
echo "✅ Creating validation setup completion..."
cat >> setup_stage4.sh << 'EOF'

# Make test scripts executable
echo "🔧 Making test scripts executable..."
chmod +x tests/validation/test_data_accuracy.py
chmod +x tests/validation/test_reliability.py
chmod +x tests/performance/test_performance.py
chmod +x tests/data_quality/test_data_quality.py
chmod +x tests/integration/test_end_to_end.py
chmod +x tests/run_all_tests.py

# Create sample test data directory with proper structure
echo "📁 Setting up test data structure..."
mkdir -p tests/fixtures/sample_data/{exports,backups}
mkdir -p logs/tests

# Create quick validation script
echo "⚡ Creating quick validation script..."
cat > quick_validate.sh << 'VALIDATE_EOF'
#!/bin/bash

# Quick validation script for SofaScore pipeline
echo "SofaScore Pipeline - Quick Validation"
echo "===================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $(basename $VIRTUAL_ENV)"
else
    echo "❌ Virtual environment not active"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Run essential tests only
echo -e "\n🔍 Running essential validation tests..."

echo -e "\n1. Database Connection Test:"
python -c "
from config.database import test_connection
if test_connection():
    print('   ✅ Database connection successful')
else:
    print('   ❌ Database connection failed')
    exit(1)
"

echo -e "\n2. Data Quality Check:"
python -c "
from config.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM live_matches'))
        matches = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM goal_events'))
        goals = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM fixtures'))
        fixtures = result.scalar()
    print(f'   ✅ Data counts: {matches} matches, {goals} goals, {fixtures} fixtures')
except Exception as e:
    print(f'   ❌ Data quality check failed: {e}')
    exit(1)
"

echo -e "\n3. API Connectivity Test:"
python -c "
from src.fixture_scraper import FixtureScraper
from datetime import datetime
try:
    scraper = FixtureScraper()
    fixtures = scraper.get_fixtures_by_date(datetime.now().strftime('%Y-%m-%d'))
    print(f'   ✅ API connectivity successful (found {len(fixtures)} fixtures)')
except Exception as e
# Make test scripts executable
echo "🔧 Making test scripts executable..."
chmod +x tests/validation/test_data_accuracy.py
chmod +x tests/validation/test_reliability.py
chmod +x tests/performance/test_performance.py
chmod +x tests/data_quality/test_data_quality.py
chmod +x tests/integration/test_end_to_end.py
chmod +x tests/run_all_tests.py

# Create sample test data directory with proper structure
echo "📁 Setting up test data structure..."
mkdir -p tests/fixtures/sample_data/{exports,backups}
mkdir -p logs/tests

# Create quick validation script
echo "⚡ Creating quick validation script..."
cat > quick_validate.sh << 'VALIDATE_EOF'
#!/bin/bash

# Quick validation script for SofaScore pipeline
echo "SofaScore Pipeline - Quick Validation"
echo "===================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $(basename $VIRTUAL_ENV)"
else
    echo "❌ Virtual environment not active"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Run essential tests only
echo -e "\n🔍 Running essential validation tests..."

echo -e "\n1. Database Connection Test:"
python -c "
from config.database import test_connection
if test_connection():
    print('   ✅ Database connection successful')
else:
    print('   ❌ Database connection failed')
    exit(1)
"

echo -e "\n2. Data Quality Check:"
python -c "
from config.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM live_matches'))
        matches = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM goal_events'))
        goals = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM fixtures'))
        fixtures = result.scalar()
    print(f'   ✅ Data counts: {matches} matches, {goals} goals, {fixtures} fixtures')
except Exception as e:
    print(f'   ❌ Data quality check failed: {e}')
    exit(1)
"

echo -e "\n3. API Connectivity Test:"
python -c "
from src.fixture_scraper import FixtureScraper
from datetime import datetime
try:
    scraper = FixtureScraper()
    fixtures = scraper.get_fixtures_by_date(datetime.now().strftime('%Y-%m-%d'))
    print(f'   ✅ API connectivity successful (found {len(fixtures)} fixtures)')
except Exception as e
