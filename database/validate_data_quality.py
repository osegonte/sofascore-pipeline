#!/usr/bin/env python3
"""
Data Quality Validator for SofaScore Pipeline
Checks all required fields are populated and validates data integrity
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text

class DataQualityValidator:
    """Validates data quality and completeness"""
    
    def __init__(self):
        self.engine = engine
        self.required_fields = {
            'live_matches': ['match_id', 'home_team', 'away_team', 'competition'],
            'goal_events': ['goal_id', 'match_id', 'exact_timestamp', 'team_side'],
            'team_statistics': ['match_id', 'team_side'],
            'player_statistics': ['match_id', 'player_name', 'team_side'],
            'fixtures': ['fixture_id', 'home_team', 'away_team']
        }
        
        self.critical_fields = {
            'live_matches': ['venue', 'competition', 'home_score', 'away_score'],
            'team_statistics': ['possession_percentage', 'shots_on_target', 'total_shots'],
            'goal_events': ['scoring_player', 'total_minute', 'time_interval'],
            'player_statistics': ['goals', 'assists', 'is_starter']
        }
    
    def validate_all_tables(self):
        """Validate all tables and generate report"""
        print("🔍 Data Quality Validation Report")
        print("=" * 50)
        
        total_score = 0
        max_score = 0
        
        for table in self.required_fields.keys():
            score, max_table_score = self.validate_table(table)
            total_score += score
            max_score += max_table_score
        
        overall_score = (total_score / max_score) * 100 if max_score > 0 else 0
        
        print(f"\n📊 OVERALL DATA QUALITY SCORE: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            print("✅ EXCELLENT - Production ready!")
        elif overall_score >= 75:
            print("🟨 GOOD - Minor improvements needed")
        elif overall_score >= 60:
            print("🟧 FAIR - Some critical issues to fix")
        else:
            print("❌ POOR - Major data quality issues")
        
        return overall_score
    
    def validate_table(self, table_name):
        """Validate individual table"""
        print(f"\n📋 Validating {table_name}...")
        
        try:
            with self.engine.connect() as conn:
                # Get table info
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                total_records = result.scalar()
                
                if total_records == 0:
                    print(f"   ⚠️  Empty table - 0 records")
                    return 0, 100
                
                print(f"   📊 Total records: {total_records}")
                
                # Check required fields
                required_score = self._check_required_fields(conn, table_name, total_records)
                
                # Check critical fields completeness
                critical_score = self._check_critical_fields(conn, table_name, total_records)
                
                # Check data consistency
                consistency_score = self._check_data_consistency(conn, table_name)
                
                table_score = (required_score + critical_score + consistency_score) / 3
                print(f"   🎯 Table Score: {table_score:.1f}/100")
                
                return table_score, 100
                
        except Exception as e:
            print(f"   ❌ Error validating {table_name}: {e}")
            return 0, 100
    
    def _check_required_fields(self, conn, table_name, total_records):
        """Check required fields are not null"""
        required_fields = self.required_fields.get(table_name, [])
        if not required_fields:
            return 100
        
        null_counts = {}
        for field in required_fields:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE {field} IS NULL"))
                null_count = result.scalar()
                null_counts[field] = null_count
            except Exception:
                null_counts[field] = total_records  # Assume all null if error
        
        total_null = sum(null_counts.values())
        total_possible = len(required_fields) * total_records
        
        if total_possible == 0:
            score = 100
        else:
            score = ((total_possible - total_null) / total_possible) * 100
        
        print(f"   ✓ Required fields: {score:.1f}% complete")
        
        for field, null_count in null_counts.items():
            if null_count > 0:
                pct = (null_count / total_records) * 100
                print(f"     ⚠️  {field}: {null_count} nulls ({pct:.1f}%)")
        
        return score
    
    def _check_critical_fields(self, conn, table_name, total_records):
        """Check critical fields completeness"""
        critical_fields = self.critical_fields.get(table_name, [])
        if not critical_fields:
            return 100
        
        null_counts = {}
        for field in critical_fields:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE {field} IS NULL"))
                null_count = result.scalar()
                null_counts[field] = null_count
            except Exception:
                null_counts[field] = total_records
        
        total_null = sum(null_counts.values())
        total_possible = len(critical_fields) * total_records
        
        if total_possible == 0:
            score = 100
        else:
            score = ((total_possible - total_null) / total_possible) * 100
        
        print(f"   ✓ Critical fields: {score:.1f}% complete")
        
        return score
    
    def _check_data_consistency(self, conn, table_name):
        """Check data consistency"""
        score = 100
        
        try:
            if table_name == 'goal_events':
                # Check goal timing consistency
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM goal_events 
                    WHERE exact_timestamp < 0 OR exact_timestamp > 120
                """))
                invalid_times = result.scalar()
                
                if invalid_times > 0:
                    print(f"     ⚠️  {invalid_times} goals with invalid timestamps")
                    score -= 10
                
            elif table_name == 'team_statistics':
                # Check possession percentages
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM team_statistics 
                    WHERE possession_percentage < 0 OR possession_percentage > 100
                """))
                invalid_possession = result.scalar()
                
                if invalid_possession > 0:
                    print(f"     ⚠️  {invalid_possession} records with invalid possession")
                    score -= 10
            
            elif table_name == 'live_matches':
                # Check score consistency
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM live_matches 
                    WHERE home_score < 0 OR away_score < 0
                """))
                invalid_scores = result.scalar()
                
                if invalid_scores > 0:
                    print(f"     ⚠️  {invalid_scores} matches with negative scores")
                    score -= 15
        
        except Exception as e:
            print(f"     ⚠️  Consistency check error: {e}")
            score -= 5
        
        print(f"   ✓ Data consistency: {score:.1f}%")
        return score
    
    def generate_detailed_report(self):
        """Generate detailed data quality report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"data_quality_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("SofaScore Pipeline - Data Quality Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add detailed analysis here
            f.write("Detailed validation results would go here...\n")
        
        print(f"📄 Detailed report saved: {report_file}")

def main():
    """Main validation function"""
    validator = DataQualityValidator()
    score = validator.validate_all_tables()
    
    if score >= 75:
        print("\n🎉 Data quality validation passed!")
        return 0
    else:
        print("\n❌ Data quality issues detected - review and fix")
        return 1

if __name__ == "__main__":
    sys.exit(main())
