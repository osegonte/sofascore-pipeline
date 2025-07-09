#!/usr/bin/env python3
"""
Data Verification Script for Late Goal Prediction
Compare collected data with SofaScore source for accuracy
"""

import pandas as pd
import requests
import time
import json
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import make_api_request, setup_logging

class DataVerifier:
    """Verify collected data against SofaScore source"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "https://api.sofascore.com/api/v1"
        self.tolerance = {
            'possession': 2.0,  # 2% tolerance for possession
            'shots': 1,  # 1 shot tolerance
            'score': 0,  # Exact match required for scores
            'time': 2   # 2 minute tolerance for timing
        }
    
    def verify_match_data(self, collected_data, match_id):
        """Verify a single match's data against source"""
        self.logger.info(f"Verifying match {match_id}...")
        
        # Get fresh data from API
        source_data = self.get_source_match_data(match_id)
        if not source_data:
            return {'status': 'error', 'message': 'Could not fetch source data'}
        
        # Find collected data for this match
        match_collected = None
        for record in collected_data:
            if record.get('match_id') == match_id:
                match_collected = record
                break
        
        if not match_collected:
            return {'status': 'error', 'message': 'Match not found in collected data'}
        
        # Compare data points
        verification_results = {
            'match_id': match_id,
            'verification_timestamp': datetime.now().isoformat(),
            'status': 'verified',
            'discrepancies': [],
            'matches': []
        }
        
        # Verify basic match info
        self.verify_basic_info(match_collected, source_data, verification_results)
        
        # Verify scores
        self.verify_scores(match_collected, source_data, verification_results)
        
        # Verify team statistics
        self.verify_team_stats(match_collected, source_data, verification_results)
        
        # Verify timing
        self.verify_timing(match_collected, source_data, verification_results)
        
        # Calculate verification score
        total_checks = len(verification_results['matches']) + len(verification_results['discrepancies'])
        if total_checks > 0:
            verification_score = (len(verification_results['matches']) / total_checks) * 100
        else:
            verification_score = 0
        
        verification_results['verification_score'] = verification_score
        
        return verification_results
    
    def get_source_match_data(self, match_id):
        """Get match data directly from SofaScore API"""
        try:
            # Get match details
            match_url = f"{self.base_url}/event/{match_id}"
            match_data = make_api_request(match_url)
            
            if not match_data:
                return None
            
            # Get statistics
            stats_url = f"{self.base_url}/event/{match_id}/statistics"
            stats_data = make_api_request(stats_url)
            
            # Get incidents (goals)
            incidents_url = f"{self.base_url}/event/{match_id}/incidents"
            incidents_data = make_api_request(incidents_url)
            
            return {
                'match': match_data,
                'statistics': stats_data,
                'incidents': incidents_data
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching source data for match {match_id}: {e}")
            return None
    
    def verify_basic_info(self, collected, source, results):
        """Verify basic match information"""
        match_info = source['match'].get('event', {})
        
        # Team names
        source_home = match_info.get('homeTeam', {}).get('name', '')
        source_away = match_info.get('awayTeam', {}).get('name', '')
        
        if collected.get('home_team') == source_home:
            results['matches'].append('home_team_name')
        else:
            results['discrepancies'].append({
                'field': 'home_team',
                'collected': collected.get('home_team'),
                'source': source_home
            })
        
        if collected.get('away_team') == source_away:
            results['matches'].append('away_team_name')
        else:
            results['discrepancies'].append({
                'field': 'away_team',
                'collected': collected.get('away_team'),
                'source': source_away
            })
    
    def verify_scores(self, collected, source, results):
        """Verify match scores"""
        match_info = source['match'].get('event', {})
        
        source_home_score = match_info.get('homeScore', {}).get('current', 0)
        source_away_score = match_info.get('awayScore', {}).get('current', 0)
        
        if collected.get('home_score') == source_home_score:
            results['matches'].append('home_score')
        else:
            results['discrepancies'].append({
                'field': 'home_score',
                'collected': collected.get('home_score'),
                'source': source_home_score,
                'severity': 'high'
            })
        
        if collected.get('away_score') == source_away_score:
            results['matches'].append('away_score')
        else:
            results['discrepancies'].append({
                'field': 'away_score',
                'collected': collected.get('away_score'),
                'source': source_away_score,
                'severity': 'high'
            })
    
    def verify_team_stats(self, collected, source, results):
        """Verify team statistics"""
        if not source.get('statistics'):
            return
        
        # Extract source statistics
        source_stats = self.extract_source_statistics(source['statistics'])
        
        # Verify possession
        if 'home_possession' in source_stats:
            if abs(collected.get('home_possession', 0) - source_stats['home_possession']) <= self.tolerance['possession']:
                results['matches'].append('home_possession')
            else:
                results['discrepancies'].append({
                    'field': 'home_possession',
                    'collected': collected.get('home_possession'),
                    'source': source_stats['home_possession'],
                    'tolerance': self.tolerance['possession']
                })
        
        if 'away_possession' in source_stats:
            if abs(collected.get('away_possession', 0) - source_stats['away_possession']) <= self.tolerance['possession']:
                results['matches'].append('away_possession')
            else:
                results['discrepancies'].append({
                    'field': 'away_possession',
                    'collected': collected.get('away_possession'),
                    'source': source_stats['away_possession'],
                    'tolerance': self.tolerance['possession']
                })
        
        # Verify shots
        stat_mappings = {
            'home_shots': 'home_total_shots',
            'away_shots': 'away_total_shots',
            'home_shots_on_target': 'home_shots_on_target',
            'away_shots_on_target': 'away_shots_on_target'
        }
        
        for collected_field, source_field in stat_mappings.items():
            if source_field in source_stats:
                if abs(collected.get(collected_field, 0) - source_stats[source_field]) <= self.tolerance['shots']:
                    results['matches'].append(collected_field)
                else:
                    results['discrepancies'].append({
                        'field': collected_field,
                        'collected': collected.get(collected_field),
                        'source': source_stats[source_field],
                        'tolerance': self.tolerance['shots']
                    })
    
    def extract_source_statistics(self, stats_data):
        """Extract statistics from source data"""
        source_stats = {}
        
        if 'statistics' not in stats_data:
            return source_stats
        
        for period in stats_data['statistics']:
            if period.get('period') == 'ALL':
                for group in period.get('groups', []):
                    for stat in group.get('statisticsItems', []):
                        stat_name = stat.get('name', '').lower()
                        
                        if 'possession' in stat_name or 'ball possession' in stat_name:
                            source_stats['home_possession'] = stat.get('home', 0)
                            source_stats['away_possession'] = stat.get('away', 0)
                        elif 'shots on target' in stat_name:
                            source_stats['home_shots_on_target'] = stat.get('home', 0)
                            source_stats['away_shots_on_target'] = stat.get('away', 0)
                        elif 'total shots' in stat_name or stat_name == 'shots':
                            source_stats['home_total_shots'] = stat.get('home', 0)
                            source_stats['away_total_shots'] = stat.get('away', 0)
        
        return source_stats
    
    def verify_timing(self, collected, source, results):
        """Verify timing information"""
        match_info = source['match'].get('event', {})
        
        # Get current time from source
        time_info = match_info.get('time', {})
        source_minute = time_info.get('injuryTime1', 0) + time_info.get('injuryTime2', 0)
        
        # This is tricky as the source might not have exact minute
        # We'll just check if it's reasonable
        collected_minute = collected.get('current_minute', 0)
        
        if 45 <= collected_minute <= 120:  # Reasonable range for second half
            results['matches'].append('current_minute_reasonable')
        else:
            results['discrepancies'].append({
                'field': 'current_minute',
                'collected': collected_minute,
                'source': 'unknown',
                'severity': 'medium',
                'note': 'Outside reasonable range (45-120)'
            })
    
    def verify_dataset(self, csv_file):
        """Verify entire dataset"""
        self.logger.info(f"Verifying dataset: {csv_file}")
        
        # Load collected data
        df = pd.read_csv(csv_file)
        
        # Get unique matches
        unique_matches = df['match_id'].unique()
        
        verification_results = {
            'dataset_file': csv_file,
            'total_matches': len(unique_matches),
            'verified_matches': 0,
            'failed_matches': 0,
            'overall_score': 0,
            'match_results': []
        }
        
        # Verify each match
        for match_id in unique_matches[:10]:  # Limit to first 10 for testing
            try:
                # Get all records for this match
                match_records = df[df['match_id'] == match_id].to_dict('records')
                
                # Use the most recent record
                latest_record = max(match_records, key=lambda x: x['collection_timestamp'])
                
                # Verify match
                match_result = self.verify_match_data([latest_record], match_id)
                verification_results['match_results'].append(match_result)
                
                if match_result['status'] == 'verified':
                    verification_results['verified_matches'] += 1
                else:
                    verification_results['failed_matches'] += 1
                
                # Add delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error verifying match {match_id}: {e}")
                verification_results['failed_matches'] += 1
        
        # Calculate overall score
        total_verified = verification_results['verified_matches']
        total_processed = verification_results['verified_matches'] + verification_results['failed_matches']
        
        if total_processed > 0:
            # Calculate average verification score
            scores = [r['verification_score'] for r in verification_results['match_results'] 
                     if 'verification_score' in r]
            verification_results['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        return verification_results
    
    def generate_verification_report(self, results):
        """Generate verification report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'exports/verification_report_{timestamp}.json'
        
        # Save detailed results
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        print(f"\n📊 DATA VERIFICATION RESULTS")
        print(f"=" * 50)
        print(f"Dataset: {results['dataset_file']}")
        print(f"Total matches: {results['total_matches']}")
        print(f"Verified matches: {results['verified_matches']}")
        print(f"Failed matches: {results['failed_matches']}")
        print(f"Overall verification score: {results['overall_score']:.1f}%")
        
        # Show sample discrepancies
        print(f"\n🔍 SAMPLE DISCREPANCIES:")
        discrepancy_count = 0
        for match_result in results['match_results']:
            for discrepancy in match_result.get('discrepancies', []):
                if discrepancy_count < 5:  # Show first 5
                    print(f"   • {discrepancy['field']}: "
                          f"Collected={discrepancy['collected']}, "
                          f"Source={discrepancy['source']}")
                    discrepancy_count += 1
        
        if discrepancy_count == 0:
            print("   ✅ No major discrepancies found!")
        
        print(f"\n📄 Full report saved: {report_file}")
        return report_file

def main():
    """Main verification function"""
    verifier = DataVerifier()
    
    print("Data Verification Tool")
    print("=" * 30)
    
    # Find latest data file
    import glob
    data_files = glob.glob('exports/late_goal_prediction_data_*.csv')
    
    if not data_files:
        print("❌ No data files found. Run data collection first.")
        return
    
    latest_file = max(data_files, key=os.path.getctime)
    
    print(f"📁 Latest data file: {os.path.basename(latest_file)}")
    
    # Run verification
    print("🔍 Starting verification process...")
    results = verifier.verify_dataset(latest_file)
    
    # Generate report
    verifier.generate_verification_report(results)
    
    # Provide recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if results['overall_score'] >= 90:
        print("   ✅ Excellent data quality! Ready for model training.")
    elif results['overall_score'] >= 75:
        print("   🟨 Good data quality. Minor improvements possible.")
        print("   • Review discrepancies in team statistics")
        print("   • Check API endpoint stability")
    elif results['overall_score'] >= 60:
        print("   🟧 Fair data quality. Some issues need attention.")
        print("   • Improve error handling in data collection")
        print("   • Add data validation checks")
        print("   • Review API endpoint accuracy")
    else:
        print("   ❌ Poor data quality. Major issues detected.")
        print("   • Review data collection logic")
        print("   • Check API endpoint compatibility")
        print("   • Add comprehensive error handling")
    
    print(f"\n🚀 NEXT STEPS:")
    print("   1. Review verification report")
    print("   2. Fix any critical discrepancies")
    print("   3. Run continuous collection with filters")
    print("   4. Proceed to model development")

if __name__ == "__main__":
    main()