#!/usr/bin/env python3
"""
Enhanced Live Match Scraper - Better Statistics Collection
Tries multiple endpoints and focuses on matches with rich data
"""

import logging
import sys
import os
import time
import json
from datetime import datetime
import pandas as pd
import signal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import make_api_request, extract_venue_from_response, safe_get_nested, setup_logging

class EnhancedLiveMatchScraper:
    """Enhanced scraper that tries multiple statistics sources"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "https://api.sofascore.com/api/v1"
        self.monitoring = False
        self.data_buffer = []
        
        # Enhanced statistics mapping with more variations
        self.stats_mapping = {
            'ball_possession_home': ['Ball possession', 'Possession %', 'possession', 'Ball possession %'],
            'ball_possession_away': ['Ball possession', 'Possession %', 'possession', 'Ball possession %'],
            'total_shots_home': ['Total shots', 'Shots', 'shots'],
            'total_shots_away': ['Total shots', 'Shots', 'shots'],
            'shots_on_target_home': ['Shots on target', 'On target'],
            'shots_on_target_away': ['Shots on target', 'On target'],
            'shots_off_target_home': ['Shots off target', 'Off target'],
            'shots_off_target_away': ['Shots off target', 'Off target'],
            'blocked_shots_home': ['Blocked shots', 'Blocked'],
            'blocked_shots_away': ['Blocked shots', 'Blocked'],
            'passes_home': ['Passes', 'Total passes', 'passes'],
            'passes_away': ['Passes', 'Total passes', 'passes'],
            'accurate_passes_home': ['Accurate passes', 'Passes accurate'],
            'accurate_passes_away': ['Accurate passes', 'Passes accurate'],
            'fouls_home': ['Fouls', 'fouls'],
            'fouls_away': ['Fouls', 'fouls'],
            'corner_kicks_home': ['Corner kicks', 'Corners', 'corners'],
            'corner_kicks_away': ['Corner kicks', 'Corners', 'corners'],
            'yellow_cards_home': ['Yellow cards', 'Yellow'],
            'yellow_cards_away': ['Yellow cards', 'Yellow'],
            'red_cards_home': ['Red cards', 'Red'],
            'red_cards_away': ['Red cards', 'Red'],
            'offsides_home': ['Offsides', 'Offside'],
            'offsides_away': ['Offsides', 'Offside'],
            'free_kicks_home': ['Free kicks'],
            'free_kicks_away': ['Free kicks'],
            'goalkeeper_saves_home': ['Goalkeeper saves', 'Saves'],
            'goalkeeper_saves_away': ['Goalkeeper saves', 'Saves'],
            'tackles_home': ['Tackles'],
            'tackles_away': ['Tackles'],
            'interceptions_home': ['Interceptions'],
            'interceptions_away': ['Interceptions'],
            'clearances_home': ['Clearances'],
            'clearances_away': ['Clearances'],
            'crosses_home': ['Crosses'],
            'crosses_away': ['Crosses'],
            'throw_ins_home': ['Throw-ins'],
            'throw_ins_away': ['Throw-ins']
        }
        
        # Prioritize competitions that typically have rich statistics
        self.priority_competitions = [
            'UEFA Champions League',
            'UEFA Europa League', 
            'Premier League',
            'La Liga',
            'Bundesliga',
            'Serie A',
            'Ligue 1',
            'UEFA Euro',
            'FIFA World Cup',
            'FIFA Club World Cup'
        ]
        
        signal.signal(signal.SIGINT, self.stop_monitoring)
    
    def get_live_matches(self):
        """Get live matches with priority sorting"""
        url = f"{self.base_url}/sport/football/events/live"
        data = make_api_request(url)
        
        if not data:
            return []
        
        matches = []
        priority_matches = []
        
        for event in data.get('events', []):
            match_info = {
                'match_id': event.get('id'),
                'home_team': safe_get_nested(event, ['homeTeam', 'name']),
                'away_team': safe_get_nested(event, ['awayTeam', 'name']),
                'competition': safe_get_nested(event, ['tournament', 'name']),
                'category': safe_get_nested(event, ['tournament', 'category', 'name']),
                'home_score': safe_get_nested(event, ['homeScore', 'current'], 0),
                'away_score': safe_get_nested(event, ['awayScore', 'current'], 0),
                'status': safe_get_nested(event, ['status', 'description']),
                'venue': extract_venue_from_response({'event': event}) or 'Unknown'
            }
            
            # Check if this is a priority competition
            competition = match_info.get('competition', '')
            is_priority = any(priority_comp.lower() in competition.lower() 
                            for priority_comp in self.priority_competitions)
            
            if is_priority:
                priority_matches.append(match_info)
            else:
                matches.append(match_info)
        
        # Return priority matches first, then others
        return priority_matches + matches
    
    def get_enhanced_match_statistics(self, match_id):
        """Try multiple endpoints to get the best statistics"""
        
        # Try different statistics endpoints in order of preference
        endpoints = [
            f"{self.base_url}/event/{match_id}/statistics",
            f"{self.base_url}/event/{match_id}/statistics/0",  # All periods
            f"{self.base_url}/event/{match_id}/statistics/1",  # First half
            f"{self.base_url}/event/{match_id}/statistics/2",  # Second half
            f"{self.base_url}/event/{match_id}/summary",       # Summary often has stats
            f"{self.base_url}/event/{match_id}/incidents",     # May have some stats
            f"{self.base_url}/event/{match_id}"                # Basic match data
        ]
        
        best_stats = None
        stats_source = None
        
        for i, endpoint in enumerate(endpoints):
            try:
                data = make_api_request(endpoint)
                if data:
                    # Extract statistics from this endpoint
                    extracted_stats = self._extract_statistics_from_response(data)
                    
                    # Count non-zero values to determine data quality
                    non_zero_count = sum(1 for v in extracted_stats.values() if v != 0)
                    
                    if non_zero_count > 0:
                        best_stats = extracted_stats
                        stats_source = f"endpoint_{i+1}"
                        self.logger.info(f"Found {non_zero_count} statistics from endpoint {i+1}")
                        break  # Use first endpoint with actual data
                        
            except Exception as e:
                self.logger.debug(f"Endpoint {endpoint} failed: {e}")
                continue
        
        if best_stats is None:
            # Return zeros if no statistics found
            best_stats = {key: 0 for key in self.stats_mapping.keys()}
            stats_source = "no_data"
        
        return best_stats, stats_source
    
    def _extract_statistics_from_response(self, data):
        """Extract statistics from various response formats"""
        stats = {key: 0 for key in self.stats_mapping.keys()}
        
        # Method 1: Standard statistics format
        if 'statistics' in data:
            self._extract_from_statistics_array(data['statistics'], stats)
        
        # Method 2: Summary format (sometimes has different structure)
        elif 'summary' in data:
            self._extract_from_summary(data['summary'], stats)
        
        # Method 3: Incidents format (can derive some stats)
        elif 'incidents' in data:
            self._extract_from_incidents(data['incidents'], stats)
        
        # Method 4: Direct event data (basic info)
        elif 'event' in data:
            self._extract_from_event(data['event'], stats)
        
        return stats
    
    def _extract_from_statistics_array(self, statistics_array, stats):
        """Extract from standard statistics array format"""
        for period in statistics_array:
            # Prefer 'ALL' period, but accept others if that's all we have
            period_type = period.get('period', 'ALL')
            
            groups = period.get('groups', [])
            for group in groups:
                items = group.get('statisticsItems', [])
                for item in items:
                    self._map_statistic_item(item, stats)
    
    def _extract_from_summary(self, summary_data, stats):
        """Extract from summary format"""
        # Sometimes summary has statistics in different format
        if 'statistics' in summary_data:
            self._extract_from_statistics_array(summary_data['statistics'], stats)
    
    def _extract_from_incidents(self, incidents, stats):
        """Extract basic stats from incidents (goals, cards, etc.)"""
        for incident in incidents:
            incident_type = incident.get('incidentType', '')
            team_side = incident.get('teamSide', '')
            
            # Count cards
            if incident_type == 'yellowCard':
                if team_side == 'home':
                    stats['yellow_cards_home'] += 1
                elif team_side == 'away':
                    stats['yellow_cards_away'] += 1
            elif incident_type == 'redCard':
                if team_side == 'home':
                    stats['red_cards_home'] += 1
                elif team_side == 'away':
                    stats['red_cards_away'] += 1
    
    def _extract_from_event(self, event_data, stats):
        """Extract basic info from event data"""
        # This would typically just give us basic match info
        # Not much statistics available here
        pass
    
    def _map_statistic_item(self, item, stats):
        """Enhanced statistic mapping with better name matching"""
        stat_name = item.get('name', '').strip().lower()
        home_value = item.get('home')
        away_value = item.get('away')
        
        # Handle percentage values
        if isinstance(home_value, str):
            if '%' in home_value:
                try:
                    home_value = float(home_value.replace('%', ''))
                except:
                    home_value = 0
            else:
                try:
                    home_value = float(home_value)
                except:
                    home_value = 0
        
        if isinstance(away_value, str):
            if '%' in away_value:
                try:
                    away_value = float(away_value.replace('%', ''))
                except:
                    away_value = 0
            else:
                try:
                    away_value = float(away_value)
                except:
                    away_value = 0
        
        # More flexible mapping with partial string matching
        for field_name, possible_names in self.stats_mapping.items():
            for possible_name in possible_names:
                if possible_name.lower() in stat_name or stat_name in possible_name.lower():
                    if field_name.endswith('_home') and home_value is not None:
                        stats[field_name] = home_value
                        self.logger.debug(f"Mapped {stat_name} -> {field_name}: {home_value}")
                    elif field_name.endswith('_away') and away_value is not None:
                        stats[field_name] = away_value
                        self.logger.debug(f"Mapped {stat_name} -> {field_name}: {away_value}")
                    break
    
    def collect_data_cycle(self):
        """Enhanced data collection cycle"""
        self.logger.info("Starting enhanced data collection cycle...")
        
        live_matches = self.get_live_matches()
        self.logger.info(f"Found {len(live_matches)} live matches")
        
        if not live_matches:
            return
        
        cycle_data = []
        successful_collections = 0
        
        # Process more matches but prioritize those with data
        for i, match in enumerate(live_matches[:8]):  # Increased from 5 to 8
            match_id = match.get('match_id')
            if not match_id:
                continue
            
            try:
                # Get enhanced statistics
                stats, source = self.get_enhanced_match_statistics(match_id)
                
                # Count non-zero statistics
                non_zero_stats = sum(1 for v in stats.values() if v != 0)
                
                # Create record
                record = {
                    'collection_timestamp': datetime.now().isoformat(),
                    'match_id': match_id,
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'competition': match['competition'],
                    'venue': match['venue'],
                    'home_score': match['home_score'],
                    'away_score': match['away_score'],
                    'status': match['status'],
                    'stats_source': source,
                    'non_zero_stats_count': non_zero_stats,
                    **stats  # Add all statistics
                }
                
                cycle_data.append(record)
                
                if non_zero_stats > 0:
                    successful_collections += 1
                    self.logger.info(f"✅ {match['home_team']} vs {match['away_team']} - {non_zero_stats} stats")
                else:
                    self.logger.info(f"⚪ {match['home_team']} vs {match['away_team']} - basic data only")
                
            except Exception as e:
                self.logger.error(f"Error collecting data for match {match_id}: {e}")
        
        if cycle_data:
            self.data_buffer.extend(cycle_data)
            self.logger.info(f"Added {len(cycle_data)} records to buffer ({successful_collections} with statistics)")
    
    def export_data(self):
        """Export with enhanced metadata"""
        if not self.data_buffer:
            self.logger.info("No data to export")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'exports/enhanced_live_statistics_{timestamp}.csv'
        
        os.makedirs('exports', exist_ok=True)
        
        df = pd.DataFrame(self.data_buffer)
        df.to_csv(filename, index=False)
        
        # Generate summary
        total_records = len(df)
        records_with_stats = len(df[df['non_zero_stats_count'] > 0])
        avg_stats_per_record = df['non_zero_stats_count'].mean()
        
        self.logger.info(f"Exported {total_records} records to {filename}")
        self.logger.info(f"Records with statistics: {records_with_stats}/{total_records} ({records_with_stats/total_records*100:.1f}%)")
        self.logger.info(f"Average statistics per record: {avg_stats_per_record:.1f}")
        
        print(f"📁 Enhanced export: {filename}")
        print(f"📊 {records_with_stats}/{total_records} records have detailed statistics")
        print(f"📈 Average {avg_stats_per_record:.1f} statistics per match")
        
        # Clear buffer
        self.data_buffer = []
    
    def start_monitoring(self):
        """Start enhanced monitoring"""
        print("🚀 Starting ENHANCED live data collection...")
        print("🎯 Prioritizing major competitions with rich statistics")
        print("🔄 Trying multiple API endpoints per match")
        print("📊 Will collect data every 5 minutes, export every 15 minutes")
        print("🛑 Press Ctrl+C to stop")
        
        self.monitoring = True
        collection_count = 0
        
        while self.monitoring:
            try:
                # Collect data
                self.collect_data_cycle()
                collection_count += 1
                
                # Export every 3 cycles (15 minutes)
                if collection_count % 3 == 0:
                    self.export_data()
                
                # Show status
                stats_count = sum(1 for record in self.data_buffer if record.get('non_zero_stats_count', 0) > 0)
                print(f"📊 Cycle {collection_count} completed at {datetime.now().strftime('%H:%M:%S')}")
                print(f"📦 Buffer: {len(self.data_buffer)} records ({stats_count} with statistics)")
                
                # Wait 5 minutes
                print("⏱️  Waiting 5 minutes for next cycle...")
                time.sleep(300)  # 5 minutes
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping gracefully...")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
        
        # Final export
        if self.data_buffer:
            self.export_data()
        
        print("👋 Enhanced monitoring stopped")
    
    def stop_monitoring(self, signum=None, frame=None):
        """Stop monitoring"""
        self.monitoring = False

def main():
    """Main function"""
    scraper = EnhancedLiveMatchScraper()
    
    print("SofaScore Enhanced Live Match Scraper")
    print("=" * 45)
    print("🎯 Enhanced Features:")
    print("  • Tries multiple API endpoints per match")
    print("  • Prioritizes competitions with rich data")
    print("  • Better statistics extraction")
    print("  • Quality metrics for each record")
    print("  • Flexible field mapping")
    
    try:
        scraper.start_monitoring()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()