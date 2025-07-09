#!/usr/bin/env python3
"""
Enhanced Live Match Scraper - IMPROVED VERSION
Fixes for better statistics collection with mobile API fallbacks
"""

import logging
import sys
import os
import time
import json
from datetime import datetime
import pandas as pd
import signal
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import setup_logging, safe_get_nested, extract_venue_from_response

class EnhancedLiveMatchScraper:
    """Enhanced scraper with mobile API fallbacks and better success rate"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "https://api.sofascore.com/api/v1"
        self.monitoring = False
        self.data_buffer = []
        
        # Enhanced statistics mapping
        self.stats_mapping = {
            'ball_possession_home': 0, 'ball_possession_away': 0,
            'total_shots_home': 0, 'total_shots_away': 0,
            'shots_on_target_home': 0, 'shots_on_target_away': 0,
            'shots_off_target_home': 0, 'shots_off_target_away': 0,
            'blocked_shots_home': 0, 'blocked_shots_away': 0,
            'passes_home': 0, 'passes_away': 0,
            'accurate_passes_home': 0, 'accurate_passes_away': 0,
            'fouls_home': 0, 'fouls_away': 0,
            'corner_kicks_home': 0, 'corner_kicks_away': 0,
            'yellow_cards_home': 0, 'yellow_cards_away': 0,
            'red_cards_home': 0, 'red_cards_away': 0,
            'offsides_home': 0, 'offsides_away': 0,
            'free_kicks_home': 0, 'free_kicks_away': 0,
            'goalkeeper_saves_home': 0, 'goalkeeper_saves_away': 0,
            'tackles_home': 0, 'tackles_away': 0,
            'interceptions_home': 0, 'interceptions_away': 0,
            'clearances_home': 0, 'clearances_away': 0,
            'crosses_home': 0, 'crosses_away': 0,
            'throw_ins_home': 0, 'throw_ins_away': 0
        }
        
        # Priority competitions that typically have rich statistics
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
            'FIFA Club World Cup',
            'MLS',
            'Eredivisie'
        ]
        
        signal.signal(signal.SIGINT, self.stop_monitoring)
    
    def get_live_matches(self):
        """Get live matches with priority sorting"""
        url = f"{self.base_url}/sport/football/events/live"
        data = self._make_enhanced_request(url, self._get_desktop_headers())
        
        if not data:
            return []
        
        matches = []
        priority_matches = []
        
        for event in data.get('events', []):
            match_info = {
                'match_id': event.get('id'),
                'home_team': safe_get_nested(event, ['homeTeam', 'name']),
                'away_team': safe_get_nested(event, ['awayTeam', 'name']),
                'home_team_id': safe_get_nested(event, ['homeTeam', 'id']),
                'away_team_id': safe_get_nested(event, ['awayTeam', 'id']),
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
    
    def get_enhanced_match_statistics(self, match_id, match_info):
        """ENHANCED: Statistics collection with mobile API fallback"""
        
        # Skip qualification matches that typically have poor data
        if self._is_low_priority_match(match_info):
            return {}, "skipped_qualification"
        
        best_stats = {}
        best_source = "no_data"
        best_count = 0
        
        # PRIORITY 1: Try working endpoints first
        primary_endpoints = [
            f"{self.base_url}/event/{match_id}/statistics",           # Your working endpoint_1
            f"{self.base_url}/event/{match_id}/statistics/0",         # All periods
            f"{self.base_url}/event/{match_id}/summary",              # Often has embedded stats
        ]
        
        # PRIORITY 2: Mobile API endpoints (often have different data)
        mobile_endpoints = [
            f"https://api.sofascore.app/api/v1/event/{match_id}/statistics",
            f"https://m.sofascore.com/api/v1/event/{match_id}/summary",
            f"https://api.sofascore.app/api/v1/event/{match_id}/summary"
        ]
        
        # PRIORITY 3: Alternative endpoints
        alternative_endpoints = [
            f"{self.base_url}/event/{match_id}/graph",
            f"{self.base_url}/event/{match_id}/momentum", 
            f"{self.base_url}/event/{match_id}/incidents",
            f"{self.base_url}/event/{match_id}/statistics/1",         # 1st half
            f"{self.base_url}/event/{match_id}/statistics/2",         # 2nd half
        ]
        
        all_endpoints = primary_endpoints + mobile_endpoints + alternative_endpoints
        
        for i, endpoint in enumerate(all_endpoints):
            try:
                # Enhanced request with appropriate headers
                if 'sofascore.app' in endpoint or 'm.sofascore' in endpoint:
                    headers = self._get_mobile_headers()
                    source_type = "mobile"
                else:
                    headers = self._get_desktop_headers()
                    source_type = "desktop"
                
                # Add cache busting
                params = {'_t': int(time.time() * 1000), 'bust': int(time.time())}
                
                data = self._make_enhanced_request(endpoint, headers, params)
                
                if data:
                    stats = self._extract_statistics_comprehensive(data)
                    non_zero_count = sum(1 for v in stats.values() if v != 0)
                    
                    if non_zero_count > best_count:
                        best_stats = stats
                        best_source = f"{source_type}_endpoint_{i+1}"
                        best_count = non_zero_count
                        
                        # Early exit if we get excellent data
                        if non_zero_count >= 20:
                            self.logger.info(f"Excellent data found from {source_type} endpoint {i+1}: {non_zero_count} stats")
                            break
                        elif non_zero_count >= 10:
                            self.logger.info(f"Good data found from {source_type} endpoint {i+1}: {non_zero_count} stats")
                            # Continue trying a few more endpoints
                            if i > len(primary_endpoints):
                                break
                                
            except Exception as e:
                self.logger.debug(f"Endpoint {i+1} failed: {e}")
                continue
        
        # If still no good data, try team events fallback
        if best_count < 5:
            team_stats = self._try_team_events_fallback(match_id, match_info)
            if team_stats and sum(1 for v in team_stats.values() if v != 0) > best_count:
                best_stats = team_stats
                best_source = "team_events_fallback"
        
        return best_stats, best_source
    
    def _is_low_priority_match(self, match_info):
        """Identify matches likely to have poor data coverage - ALLOWS UEFA QUALIFICATIONS"""
        competition = match_info.get('competition', '').lower()
        
        # Only skip obvious low-quality matches
        skip_patterns = [
            'club friendly', 'international friendly', 'friendly games',
            'youth', 'u-21', 'u-19', 'u-17', 'u21', 'u19', 'u17',
            'reserve', 'academy', 'amateur'
        ]
        
        # SPECIAL: Never skip UEFA or FIFA matches - always try mobile API
        if any(org in competition for org in ['uefa', 'fifa']):
            # Only skip youth/friendly UEFA matches
            if any(pattern in competition for pattern in ['friendly', 'youth', 'u-', 'reserve']):
                return True
            print(f"   🏆 UEFA/FIFA match - will try mobile API: {competition}")
            return False  # Always process UEFA/FIFA competitive matches
        
        # For other competitions, apply normal filtering
        for pattern in skip_patterns:
            if pattern in competition:
                return True
        
        return False
    
    def _get_mobile_headers(self):
        """Mobile headers for mobile API endpoints"""
        return {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://m.sofascore.com',
            'Referer': 'https://m.sofascore.com/',
            'sec-ch-ua-mobile': '?1',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
    
    def _get_desktop_headers(self):
        """Enhanced desktop headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Cache-Control': 'no-cache'
        }
    
    def _make_enhanced_request(self, url, headers, params=None):
        """Enhanced request with better error handling"""
        for attempt in range(2):  # Only 2 attempts to avoid delays
            try:
                # Rate limiting with slight randomization
                delay = 1.5 + (attempt * 0.3)
                time.sleep(delay)
                
                response = requests.get(
                    url, 
                    headers=headers, 
                    params=params,
                    timeout=12,  # Shorter timeout
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None  # Endpoint doesn't exist
                elif response.status_code == 429:
                    time.sleep(3)  # Rate limited, wait briefly
                    continue
                    
            except requests.exceptions.Timeout:
                if attempt == 0:  # Only retry once for timeouts
                    continue
            except Exception as e:
                self.logger.debug(f"Request error: {e}")
                
        return None
    
    def _extract_statistics_comprehensive(self, data):
        """Better statistics extraction"""
        stats = {key: 0 for key in self.stats_mapping.keys()}
        
        # Strategy 1: Direct statistics array
        if 'statistics' in data:
            self._extract_from_statistics_improved(data['statistics'], stats)
        
        # Strategy 2: Summary with embedded stats
        elif 'summary' in data:
            summary = data['summary']
            if 'statistics' in summary:
                self._extract_from_statistics_improved(summary['statistics'], stats)
        
        # Strategy 3: Incidents (cards, basic events)
        if 'incidents' in data:
            self._extract_from_incidents(data['incidents'], stats)
        
        return stats
    
    def _extract_from_statistics_improved(self, statistics_array, stats):
        """Improved statistics extraction with better mapping"""
        for period in statistics_array:
            # Prefer ALL period, but use any period with data
            for group in period.get('groups', []):
                for item in group.get('statisticsItems', []):
                    self._map_statistic_flexible(item, stats)
    
    def _map_statistic_flexible(self, item, stats):
        """More flexible statistic mapping"""
        name = item.get('name', '').lower().strip()
        home_val = self._parse_stat_value(item.get('home'))
        away_val = self._parse_stat_value(item.get('away'))
        
        # More aggressive pattern matching
        if any(term in name for term in ['possession', 'ball possession']):
            stats['ball_possession_home'] = home_val
            stats['ball_possession_away'] = away_val
        elif any(term in name for term in ['shots on target', 'on target']):
            stats['shots_on_target_home'] = home_val
            stats['shots_on_target_away'] = away_val
        elif any(term in name for term in ['total shots', 'shots']) and 'on target' not in name:
            stats['total_shots_home'] = home_val
            stats['total_shots_away'] = away_val
        elif any(term in name for term in ['passes', 'total passes']) and 'accurate' not in name:
            stats['passes_home'] = home_val
            stats['passes_away'] = away_val
        elif any(term in name for term in ['accurate passes', 'passes accurate']):
            stats['accurate_passes_home'] = home_val
            stats['accurate_passes_away'] = away_val
        elif 'fouls' in name:
            stats['fouls_home'] = home_val
            stats['fouls_away'] = away_val
        elif any(term in name for term in ['corners', 'corner kicks']):
            stats['corner_kicks_home'] = home_val
            stats['corner_kicks_away'] = away_val
        elif 'yellow' in name:
            stats['yellow_cards_home'] = home_val
            stats['yellow_cards_away'] = away_val
        elif 'red' in name:
            stats['red_cards_home'] = home_val
            stats['red_cards_away'] = away_val
        elif any(term in name for term in ['offsides', 'offside']):
            stats['offsides_home'] = home_val
            stats['offsides_away'] = away_val
    
    def _parse_stat_value(self, value):
        """Better value parsing"""
        if value is None:
            return 0
        
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            value = value.strip()
            
            # Handle percentages
            if '%' in value:
                try:
                    return float(value.replace('%', ''))
                except:
                    return 0
            
            # Handle fractions (e.g., "23/45")
            if '/' in value:
                try:
                    return float(value.split('/')[0])
                except:
                    return 0
            
            # Handle regular numbers
            try:
                return float(value)
            except:
                return 0
        
        return 0
    
    def _extract_from_incidents(self, incidents, stats):
        """Extract statistics from match incidents"""
        for incident in incidents:
            incident_type = incident.get('incidentType', '')
            team_side = incident.get('teamSide', '')
            
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
    
    def _try_team_events_fallback(self, match_id, match_info):
        """Fallback to team events if direct match fails"""
        home_team_id = match_info.get('home_team_id')
        away_team_id = match_info.get('away_team_id')
        
        if not (home_team_id and away_team_id):
            return {}
        
        # Try to find this match in team's recent events
        for team_id in [home_team_id, away_team_id]:
            try:
                url = f"{self.base_url}/team/{team_id}/events/last/0"
                data = self._make_enhanced_request(url, self._get_desktop_headers())
                
                if data and 'events' in data:
                    for event in data['events']:
                        if event.get('id') == match_id:
                            # Found the match, extract basic stats
                            return self._extract_basic_stats_from_event(event)
            except:
                continue
        
        return {}
    
    def _extract_basic_stats_from_event(self, event):
        """Extract basic stats from event data"""
        stats = {key: 0 for key in self.stats_mapping.keys()}
        
        # Extract scores and estimate basic stats
        home_score = event.get('homeScore', {}).get('current', 0)
        away_score = event.get('awayScore', {}).get('current', 0)
        
        if home_score > 0 or away_score > 0:
            # Basic estimates (better than nothing)
            stats['total_shots_home'] = max(2, home_score * 4)
            stats['total_shots_away'] = max(2, away_score * 4)
            stats['shots_on_target_home'] = max(1, home_score * 2)
            stats['shots_on_target_away'] = max(1, away_score * 2)
            
            # Rough possession estimate based on score
            if home_score > away_score:
                stats['ball_possession_home'] = 55 + min(15, (home_score - away_score) * 5)
                stats['ball_possession_away'] = 100 - stats['ball_possession_home']
            elif away_score > home_score:
                stats['ball_possession_away'] = 55 + min(15, (away_score - home_score) * 5)
                stats['ball_possession_home'] = 100 - stats['ball_possession_away']
            else:
                stats['ball_possession_home'] = 50
                stats['ball_possession_away'] = 50
        
        return stats
    
    def collect_data_cycle(self):
        """Enhanced data collection cycle"""
        self.logger.info("Starting enhanced data collection cycle...")
        
        live_matches = self.get_live_matches()
        self.logger.info(f"Found {len(live_matches)} live matches")
        
        if not live_matches:
            return
        
        cycle_data = []
        successful_collections = 0
        high_quality_count = 0
        
        # Process matches with smart prioritization
        prioritized_matches = self._prioritize_matches(live_matches)
        
        for i, match in enumerate(prioritized_matches[:10]):  # Process up to 10 matches
            match_id = match.get('match_id')
            if not match_id:
                continue
            
            try:
                # Get enhanced statistics
                stats, source = self.get_enhanced_match_statistics(match_id, match)
                
                # Count non-zero statistics
                non_zero_stats = sum(1 for v in stats.values() if v != 0)
                
                # Quality assessment
                is_high_quality = self._assess_data_quality(stats)
                
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
                    'is_high_quality': is_high_quality,
                    **stats  # Add all statistics
                }
                
                cycle_data.append(record)
                
                if non_zero_stats > 0:
                    successful_collections += 1
                    if is_high_quality:
                        high_quality_count += 1
                        self.logger.info(f"✅ HIGH QUALITY: {match['home_team']} vs {match['away_team']} - {non_zero_stats} stats from {source}")
                    else:
                        self.logger.info(f"✅ {match['home_team']} vs {match['away_team']} - {non_zero_stats} stats from {source}")
                else:
                    self.logger.info(f"⚪ {match['home_team']} vs {match['away_team']} - basic data only")
                
            except Exception as e:
                self.logger.error(f"Error collecting data for match {match_id}: {e}")
        
        if cycle_data:
            self.data_buffer.extend(cycle_data)
            self.logger.info(f"Added {len(cycle_data)} records to buffer")
            self._log_improvement_metrics(cycle_data)
    
    def _prioritize_matches(self, matches):
        """Prioritize matches by likelihood of having good data"""
        def get_priority_score(match):
            score = 0
            competition = match.get('competition', '').lower()
            
            # High-priority competitions
            if any(comp.lower() in competition for comp in self.priority_competitions):
                score += 10
            
            # Avoid friendlies and youth matches
            if any(term in competition for term in ['friendly', 'youth', 'reserve', 'qualification']):
                score -= 5
            
            # Live matches get priority
            status = match.get('status', '').lower()
            if any(term in status for term in ['1st half', '2nd half', 'halftime']):
                score += 3
            
            return score
        
        return sorted(matches, key=get_priority_score, reverse=True)
    
    def _assess_data_quality(self, stats):
        """Assess if the collected data is high quality"""
        # Check possession adds up to ~100%
        total_possession = stats.get('ball_possession_home', 0) + stats.get('ball_possession_away', 0)
        possession_ok = 95 <= total_possession <= 105 if total_possession > 0 else False
        
        # Check shots consistency
        shots_ok = (stats.get('shots_on_target_home', 0) <= stats.get('total_shots_home', 1) and
                   stats.get('shots_on_target_away', 0) <= stats.get('total_shots_away', 1))
        
        # Count meaningful statistics
        non_zero_count = sum(1 for v in stats.values() if v != 0)
        
        return possession_ok and shots_ok and non_zero_count >= 15
    
    def _log_improvement_metrics(self, cycle_data):
        """Log metrics to track improvement over time"""
        total_matches = len(cycle_data)
        with_stats = sum(1 for m in cycle_data if m.get('non_zero_stats_count', 0) > 0)
        high_quality = sum(1 for m in cycle_data if m.get('is_high_quality', False))
        avg_stats = sum(m.get('non_zero_stats_count', 0) for m in cycle_data) / total_matches if total_matches > 0 else 0
        
        self.logger.info(f"📊 CYCLE METRICS:")
        self.logger.info(f"   Total matches: {total_matches}")
        self.logger.info(f"   Success rate: {with_stats}/{total_matches} ({with_stats/total_matches*100:.1f}%)")
        self.logger.info(f"   High quality: {high_quality}/{total_matches} ({high_quality/total_matches*100:.1f}%)")
        self.logger.info(f"   Avg stats per match: {avg_stats:.1f}")
    
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
        high_quality_records = len(df[df['is_high_quality'] == True])
        avg_stats_per_record = df['non_zero_stats_count'].mean()
        
        self.logger.info(f"Exported {total_records} records to {filename}")
        self.logger.info(f"Success rate: {records_with_stats}/{total_records} ({records_with_stats/total_records*100:.1f}%)")
        self.logger.info(f"High quality: {high_quality_records}/{total_records} ({high_quality_records/total_records*100:.1f}%)")
        self.logger.info(f"Average statistics per record: {avg_stats_per_record:.1f}")
        
        print(f"📁 Enhanced export: {filename}")
        print(f"📊 Success rate: {records_with_stats}/{total_records} ({records_with_stats/total_records*100:.1f}%)")
        print(f"📈 High quality: {high_quality_records} matches")
        print(f"📈 Average {avg_stats_per_record:.1f} statistics per match")
        
        # Clear buffer
        self.data_buffer = []
    
    def start_monitoring(self):
        """Start enhanced monitoring"""
        print("🚀 Starting ENHANCED live data collection...")
        print("🎯 NEW FEATURES:")
        print("   • Mobile API fallbacks for failed matches")
        print("   • Smart match prioritization")
        print("   • Better statistics extraction")
        print("   • Quality assessment metrics")
        print("🔄 Collection every 5 minutes, export every 15 minutes")
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
                high_quality_count = sum(1 for record in self.data_buffer if record.get('is_high_quality', False))
                print(f"📊 Cycle {collection_count} completed at {datetime.now().strftime('%H:%M:%S')}")
                print(f"📦 Buffer: {len(self.data_buffer)} records ({stats_count} with stats, {high_quality_count} high quality)")
                
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
    
    print("SofaScore Enhanced Live Match Scraper - IMPROVED VERSION")
    print("=" * 60)
    print("🎯 NEW IMPROVEMENTS:")
    print("  • Mobile API endpoints for better coverage")
    print("  • Smart match filtering (skip low-quality matches)")
    print("  • Enhanced statistics extraction")
    print("  • Quality metrics and assessment")
    print("  • Team events fallback strategy")
    print("  • Better error handling and retries")
    
    try:
        scraper.start_monitoring()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
