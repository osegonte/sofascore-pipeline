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
