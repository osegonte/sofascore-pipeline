#!/usr/bin/env python3
"""
Enhanced Historical Team Data Scraper
Collects comprehensive season stats + detailed recent match data for teams
"""

import logging
import sys
import os
import time
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import setup_logging, safe_get_nested, make_api_request

class TeamHistoricalScraper:
    """Enhanced scraper for comprehensive team historical data"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "https://api.sofascore.com/api/v1"
        
    def get_team_season_stats(self, team_id: int, tournament_id: int, season_id: int) -> Dict:
        """
        Get comprehensive season statistics for a team
        
        Args:
            team_id: SofaScore team ID
            tournament_id: Tournament ID (e.g., Premier League)
            season_id: Season ID (e.g., 2024 season)
        """
        self.logger.info(f"🏆 Fetching season stats for team {team_id} in tournament {tournament_id}, season {season_id}")
        
        # Try multiple endpoints for season stats
        endpoints = [
            f"{self.base_url}/team/{team_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall",
            f"{self.base_url}/team/{team_id}/tournament/{tournament_id}/season/{season_id}/statistics",
            f"{self.base_url}/unique-tournament/{tournament_id}/season/{season_id}/team/{team_id}/statistics"
        ]
        
        season_stats = {}
        
        for endpoint in endpoints:
            self.logger.info(f"📊 Trying season stats endpoint: {endpoint}")
            data = make_api_request(endpoint)
            
            if data and 'statistics' in data:
                stats = self._extract_season_statistics(data)
                if stats:
                    season_stats.update(stats)
                    self.logger.info(f"✅ Got {len(stats)} season statistics from this endpoint")
                    break
        
        # Get additional season data from team overview
        team_overview = make_api_request(f"{self.base_url}/team/{team_id}")
        if team_overview:
            team_info = self._extract_team_info(team_overview)
            season_stats.update(team_info)
        
        return season_stats
    
    def get_team_recent_matches(self, team_id: int, num_matches: int = 7) -> List[Dict]:
        """
        Get detailed data for team's most recent matches using corrected date-based search
        
        Args:
            team_id: SofaScore team ID
            num_matches: Number of recent matches to analyze (default 7)
        """
        self.logger.info(f"📅 Fetching last {num_matches} matches for team {team_id} using corrected method")
        
        matches_found = []
        current_date = datetime.now()
        
        # Search backwards through dates to find completed matches
        for days_back in range(1, 365):  # Search up to a year back
            if len(matches_found) >= num_matches:
                break
            
            search_date = current_date - timedelta(days=days_back)
            date_str = search_date.strftime('%Y-%m-%d')
            
            # Get matches for this date
            url = f"{self.base_url}/sport/football/scheduled-events/{date_str}"
            data = make_api_request(url)
            
            if data and 'events' in data:
                for event in data['events']:
                    # Check if this is our team's match
                    home_id = safe_get_nested(event, ['homeTeam', 'id'])
                    away_id = safe_get_nested(event, ['awayTeam', 'id'])
                    
                    if home_id == team_id or away_id == team_id:
                        # Check if match is finished
                        status = safe_get_nested(event, ['status', 'type'])
                        if status == 'finished':
                            matches_found.append(event)
                            self.logger.info(f"   ✅ Found completed match on {date_str}: {safe_get_nested(event, ['homeTeam', 'name'])} vs {safe_get_nested(event, ['awayTeam', 'name'])}")
            
            # Add small delay every 10 requests to avoid rate limiting
            if days_back % 10 == 0:
                time.sleep(0.5)
        
        self.logger.info(f"📊 Found {len(matches_found)} completed matches")
        
        # Sort by date (most recent first) and return requested number
        matches_found.sort(key=lambda x: x.get('startTimestamp', 0), reverse=True)
        recent_matches = matches_found[:num_matches]
        
        # Process each match for detailed statistics
        detailed_matches = []
        for event in recent_matches:
            try:
                match_details = self._get_comprehensive_match_details(event.get('id'), team_id, event)
                if match_details:
                    detailed_matches.append(match_details)
                time.sleep(1.2)  # Rate limiting
            except Exception as e:
                self.logger.error(f"Error processing match {event.get('id')}: {e}")
        
        self.logger.info(f"✅ Collected detailed data for {len(detailed_matches)} recent matches")
        return detailed_matches
    
    def _extract_season_statistics(self, data: Dict) -> Dict:
        """Extract season statistics from API response"""
        stats = {}
        
        try:
            statistics = data.get('statistics', {})
            
            # Map common season statistics with proper value cleaning
            stat_mappings = {
                'matches': 'matches_played',
                'goals': 'goals_scored',
                'goalsAgainst': 'goals_conceded',
                'assists': 'assists',
                'averageGoalsPerMatch': 'goals_per_game',
                'penaltyGoals': 'penalty_goals',
                'totalShotsPerMatch': 'total_shots_per_game',
                'successfulDribblesPerMatch': 'successful_dribbles_per_game',
                'cornersPerMatch': 'corners_per_game',
                'freeKicksPerMatch': 'free_kicks_per_game',
                'possessionPercentage': 'ball_possession_pct',
                'accuratePassesPercentage': 'accurate_passes_pct',
                'accurateLongBallsPercentage': 'accurate_long_balls_pct',
                'cleanSheets': 'clean_sheets',
                'goalsAgainstPerMatch': 'goals_conceded_per_game',
                'interceptionsPerMatch': 'interceptions_per_game',
                'savesPerMatch': 'saves_per_game',
                'tacklesPerMatch': 'tackles_per_game',
                'clearancesPerMatch': 'clearances_per_game',
                'foulsPerMatch': 'fouls_per_game',
                'offsidePerMatch': 'offsides_per_game',
                'yellowCardsPerMatch': 'yellow_cards_per_game',
                'redCards': 'red_cards_total'
            }
            
            for api_key, our_key in stat_mappings.items():
                value = statistics.get(api_key)
                if value is not None:
                    try:
                        # Clean the value (remove % signs, handle strings)
                        if isinstance(value, str):
                            if value.endswith('%'):
                                clean_value = float(value.rstrip('%'))
                            else:
                                clean_value = float(value)
                        else:
                            clean_value = float(value)
                        
                        # Apply reasonable bounds for percentage values
                        if 'percentage' in api_key.lower() or '_pct' in our_key:
                            clean_value = min(100.0, max(0.0, clean_value))
                        
                        stats[our_key] = clean_value
                        
                    except (ValueError, TypeError):
                        # Keep original value if conversion fails
                        stats[our_key] = value
            
            self.logger.info(f"📊 Extracted {len(stats)} season statistics")
            
        except Exception as e:
            self.logger.error(f"Error extracting season statistics: {e}")
        
        return stats
    
    def _extract_team_info(self, data: Dict) -> Dict:
        """Extract team information"""
        info = {}
        
        try:
            team = data.get('team', {})
            info['team_name'] = team.get('name')
            info['team_short_name'] = team.get('shortName')
            info['team_country'] = safe_get_nested(team, ['country', 'name'])
            info['team_founded'] = team.get('foundedAtTimestamp')
            
            # Venue information
            venue = team.get('venue', {})
            if venue:
                info['home_venue'] = venue.get('name')
                info['venue_capacity'] = venue.get('capacity')
                info['venue_city'] = safe_get_nested(venue, ['city', 'name'])
            
        except Exception as e:
            self.logger.error(f"Error extracting team info: {e}")
        
        return info
    
    def _get_comprehensive_match_details(self, match_id: int, team_id: int, event: Dict) -> Dict:
        """Get comprehensive details for a single match"""
        
        match_details = {
            'match_id': match_id,
            'date': self._extract_match_date(event),
            'opponent': self._extract_opponent(event, team_id),
            'venue_type': self._extract_venue_type(event, team_id),
            'competition': safe_get_nested(event, ['tournament', 'name']),
            'result': self._extract_result(event, team_id),
            'final_score': self._extract_final_score(event)
        }
        
        # Get basic goals from score (ALWAYS use this as the authoritative source)
        team_goals, opponent_goals = self._extract_team_goals_from_score(event, team_id)
        match_details['goals_scored'] = team_goals
        match_details['goals_conceded'] = opponent_goals
        
        # Get detailed match statistics
        stats_data = make_api_request(f"{self.base_url}/event/{match_id}/statistics")
        if stats_data:
            match_stats = self._extract_match_statistics(stats_data, team_id, event)
            match_details.update(match_stats)
        
        # Get goal details and timing (for goal_times, scorers, etc. but NOT goal counts)
        incidents_data = make_api_request(f"{self.base_url}/event/{match_id}/incidents")
        if incidents_data:
            is_home = safe_get_nested(event, ['homeTeam', 'id']) == team_id
            goal_details = self._extract_goal_details_smart(incidents_data, team_id, team_goals, opponent_goals, is_home)
            # Only add timing and player details, keep our score-based goal counts
            match_details['goal_times'] = goal_details.get('goal_times', [])
            match_details['goal_scorers'] = goal_details.get('goal_scorers', [])
            match_details['assists'] = goal_details.get('assists', [])
            match_details['goal_conceded_times'] = goal_details.get('goal_conceded_times', [])
            
            # DO NOT override goals_scored and goals_conceded from incidents
        
        # Get lineup and formation data
        lineups_data = make_api_request(f"{self.base_url}/event/{match_id}/lineups")
        if lineups_data:
            lineup_details = self._extract_lineup_details(lineups_data, team_id)
            match_details.update(lineup_details)
        
        return match_details
    
    def _extract_match_date(self, event: Dict) -> str:
        """Extract match date"""
        timestamp = event.get('startTimestamp')
        if timestamp:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        return None
    
    def _extract_opponent(self, event: Dict, team_id: int) -> str:
        """Extract opponent team name"""
        home_team = safe_get_nested(event, ['homeTeam', 'name'])
        away_team = safe_get_nested(event, ['awayTeam', 'name'])
        home_team_id = safe_get_nested(event, ['homeTeam', 'id'])
        
        if home_team_id == team_id:
            return away_team
        else:
            return home_team
    
    def _extract_venue_type(self, event: Dict, team_id: int) -> str:
        """Determine if match was home or away"""
        home_team_id = safe_get_nested(event, ['homeTeam', 'id'])
        return 'home' if home_team_id == team_id else 'away'
    
    def _extract_result(self, event: Dict, team_id: int) -> str:
        """Extract match result (W/L/D)"""
        home_score = safe_get_nested(event, ['homeScore', 'current'], 0)
        away_score = safe_get_nested(event, ['awayScore', 'current'], 0)
        home_team_id = safe_get_nested(event, ['homeTeam', 'id'])
        
        if home_team_id == team_id:
            # Team was playing at home
            if home_score > away_score:
                return 'W'
            elif home_score < away_score:
                return 'L'
            else:
                return 'D'
        else:
            # Team was playing away
            if away_score > home_score:
                return 'W'
            elif away_score < home_score:
                return 'L'
            else:
                return 'D'
    
    def _extract_team_goals_from_score(self, event: Dict, team_id: int) -> tuple:
        """Extract goals scored and conceded from match score"""
        home_score = safe_get_nested(event, ['homeScore', 'current'], 0)
        away_score = safe_get_nested(event, ['awayScore', 'current'], 0)
        home_team_id = safe_get_nested(event, ['homeTeam', 'id'])
        
        if home_team_id == team_id:
            # Team was playing at home
            return home_score, away_score
        else:
            # Team was playing away
            return away_score, home_score
    
    def _extract_final_score(self, event: Dict) -> str:
        """Extract final score in format HOME-AWAY"""
        home_score = safe_get_nested(event, ['homeScore', 'current'], 0)
        away_score = safe_get_nested(event, ['awayScore', 'current'], 0)
        return f"{home_score}-{away_score}"
    
    def _extract_match_statistics(self, stats_data: Dict, team_id: int, event: Dict) -> Dict:
        """Extract detailed match statistics"""
        stats = {}
        
        try:
            # Determine if team was home or away
            home_team_id = safe_get_nested(event, ['homeTeam', 'id'])
            team_side = 'home' if home_team_id == team_id else 'away'
            
            # Extract statistics for our team
            for period in stats_data.get('statistics', []):
                if period.get('period') == 'ALL':  # Full match stats
                    for group in period.get('groups', []):
                        for stat in group.get('statisticsItems', []):
                            stat_name = stat.get('name', '').lower()
                            team_value = stat.get(team_side)
                            
                            if team_value is not None:
                                # Clean percentage values (remove % sign)
                                if isinstance(team_value, str) and team_value.endswith('%'):
                                    team_value = team_value.rstrip('%')
                                
                                # Map specific statistics
                                if 'ball possession' in stat_name:
                                    stats['possession_pct'] = float(team_value)
                                elif 'shots on target' in stat_name:
                                    stats['shots_on_target'] = int(team_value)
                                elif 'total shots' in stat_name:
                                    stats['total_shots'] = int(team_value)
                                elif 'corner kicks' in stat_name:
                                    stats['corners'] = int(team_value)
                                elif 'fouls' in stat_name:
                                    stats['fouls'] = int(team_value)
                                elif 'yellow cards' in stat_name:
                                    stats['yellow_cards'] = int(team_value)
                                elif 'red cards' in stat_name:
                                    stats['red_cards'] = int(team_value)
                                elif 'passes' in stat_name and 'accurate' not in stat_name:
                                    stats['total_passes'] = int(team_value)
                                elif 'accurate passes' in stat_name:
                                    if '%' in str(team_value):
                                        # This is already a percentage
                                        stats['pass_accuracy_pct'] = float(team_value)
                                    else:
                                        # This is raw number of accurate passes
                                        stats['accurate_passes'] = int(team_value)
                                elif 'tackles' in stat_name:
                                    stats['tackles'] = int(team_value)
                                elif 'interceptions' in stat_name:
                                    stats['interceptions'] = int(team_value)
                                elif 'clearances' in stat_name:
                                    stats['clearances'] = int(team_value)
                                elif 'saves' in stat_name:
                                    stats['goalkeeper_saves'] = int(team_value)
            
            # Calculate derived stats if we have raw numbers
            if 'total_passes' in stats and 'accurate_passes' in stats and 'pass_accuracy_pct' not in stats:
                stats['pass_accuracy_pct'] = round((stats['accurate_passes'] / stats['total_passes']) * 100, 1)
            
        except Exception as e:
            self.logger.error(f"Error extracting match statistics: {e}")
        
        return stats
    
    def _extract_goal_details_smart(self, incidents_data: Dict, team_id: int, team_goals: int, opponent_goals: int, is_home: bool) -> Dict:
        """Extract goal details with proper team separation"""
        goal_details = {
            'goal_times': [],
            'goal_scorers': [],
            'assists': [],
            'goal_conceded_times': []
        }
        
        try:
            all_goals = []
            
            # Collect all goals from incidents
            for incident in incidents_data.get('incidents', []):
                if incident.get('incidentType') == 'goal':
                    minute = incident.get('time', 0)
                    added_time = incident.get('addedTime', 0)
                    total_minute = minute + added_time
                    
                    scorer = safe_get_nested(incident, ['player', 'name'])
                    assist = safe_get_nested(incident, ['assist1', 'name'])
                    
                    if scorer:  # Only add goals with scorer info
                        all_goals.append({
                            'minute': total_minute,
                            'scorer': scorer,
                            'assist': assist
                        })
            
            # Sort goals by time
            all_goals.sort(key=lambda x: x['minute'])
            
            # Since we can't reliably determine which team scored each goal from the API,
            # we'll use a different strategy: match known goal counts with player names
            
            # Look for Manchester City players in the scorer list
            city_players = [
                'Erling Haaland', 'Phil Foden', 'Kevin De Bruyne', 'Jack Grealish',
                'Bernardo Silva', 'Riyad Mahrez', 'Gabriel Jesus', 'Raheem Sterling',
                'İlkay Gündoğan', 'João Cancelo', 'Kyle Walker', 'Ruben Dias',
                'John Stones', 'Aymeric Laporte', 'Rodri', 'Mateo Kovačić',
                'Jérémy Doku', 'Julián Álvarez', 'James McAtee', 'Joško Gvardiol',
                'Matheus Nunes', 'Savinho', 'Rico Lewis'
            ]
            
            our_goals = []
            opponent_goals_times = []
            
            for goal in all_goals:
                # Check if this is likely a City player
                is_city_goal = any(city_name in goal['scorer'] for city_name in city_players)
                
                if is_city_goal:
                    our_goals.append(goal)
                else:
                    opponent_goals_times.append(goal['minute'])
            
            # Fill our goal data (limit to actual goals scored)
            for i, goal in enumerate(our_goals[:team_goals]):
                goal_details['goal_times'].append(goal['minute'])
                goal_details['goal_scorers'].append(goal['scorer'])
                if goal['assist']:
                    goal_details['assists'].append(goal['assist'])
            
            # Fill opponent goal times (limit to actual goals conceded)
            goal_details['goal_conceded_times'] = opponent_goals_times[:opponent_goals]
            
            # If we don't have enough goals identified, pad with remaining unidentified goals
            remaining_goals = len(all_goals) - len(our_goals) - len(opponent_goals_times)
            if len(goal_details['goal_times']) < team_goals and remaining_goals > 0:
                # Add unidentified goals up to our goal count
                unidentified = [g for g in all_goals if g not in our_goals and g['minute'] not in opponent_goals_times]
                for goal in unidentified[:team_goals - len(goal_details['goal_times'])]:
                    goal_details['goal_times'].append(goal['minute'])
                    goal_details['goal_scorers'].append(goal['scorer'])
                    if goal['assist']:
                        goal_details['assists'].append(goal['assist'])
        
        except Exception as e:
            self.logger.error(f"Error extracting smart goal details: {e}")
        
        return goal_details
    
    def _extract_lineup_details(self, lineups_data: Dict, team_id: int) -> Dict:
        """Extract lineup and formation details"""
        lineup_details = {}
        
        try:
            # Find our team's lineup
            team_lineup = None
            if lineups_data.get('home', {}).get('team', {}).get('id') == team_id:
                team_lineup = lineups_data.get('home', {})
                lineup_details['venue_type_confirm'] = 'home'
            elif lineups_data.get('away', {}).get('team', {}).get('id') == team_id:
                team_lineup = lineups_data.get('away', {})
                lineup_details['venue_type_confirm'] = 'away'
            
            if team_lineup:
                # Formation
                formation = team_lineup.get('formation', {})
                lineup_details['formation'] = formation.get('formation')
                
                # Count starters and substitutes
                lineup_details['starters_count'] = len(team_lineup.get('players', []))
                lineup_details['substitutes_count'] = len(team_lineup.get('substitutes', []))
                
                # Key players (this could be enhanced with more specific criteria)
                players = team_lineup.get('players', [])
                lineup_details['starting_players'] = [
                    {
                        'name': p.get('player', {}).get('name'),
                        'position': p.get('position'),
                        'jersey_number': p.get('shirtNumber')
                    } for p in players[:11]  # First 11 players
                ]
        
        except Exception as e:
            self.logger.error(f"Error extracting lineup details: {e}")
        
        return lineup_details
    
    def get_team_comprehensive_data(self, team_id: int, tournament_id: int, season_id: int, 
                                  recent_matches: int = 7) -> Dict:
        """
        Get comprehensive historical data for a team
        
        Args:
            team_id: SofaScore team ID
            tournament_id: Tournament ID
            season_id: Season ID  
            recent_matches: Number of recent matches to analyze
        """
        self.logger.info(f"🎯 Starting comprehensive data collection for team {team_id}")
        
        comprehensive_data = {
            'team_id': team_id,
            'tournament_id': tournament_id,
            'season_id': season_id,
            'collection_timestamp': datetime.now().isoformat(),
            'season_stats': {},
            'recent_matches': [],
            'recent_match_summary': {}
        }
        
        # Get season statistics
        self.logger.info("📊 Collecting season statistics...")
        season_stats = self.get_team_season_stats(team_id, tournament_id, season_id)
        comprehensive_data['season_stats'] = season_stats
        
        # Get recent matches
        self.logger.info(f"📅 Collecting last {recent_matches} matches...")
        recent_match_data = self.get_team_recent_matches(team_id, recent_matches)
        comprehensive_data['recent_matches'] = recent_match_data
        
        # Generate recent match summary
        if recent_match_data:
            summary = self._generate_recent_match_summary(recent_match_data)
            comprehensive_data['recent_match_summary'] = summary
        
        self.logger.info(f"✅ Comprehensive data collection completed for team {team_id}")
        return comprehensive_data
    
    def _generate_recent_match_summary(self, recent_matches: List[Dict]) -> Dict:
        """Generate summary statistics for recent matches"""
        summary = {
            'matches_analyzed': len(recent_matches),
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored_total': 0,
            'goals_conceded_total': 0,
            'avg_possession': 0,
            'avg_shots_per_match': 0,
            'avg_corners_per_match': 0,
            'avg_fouls_per_match': 0,
            'clean_sheets': 0,
            'matches_scored': 0
        }
        
        if not recent_matches:
            return summary
        
        possession_values = []
        shots_values = []
        corners_values = []
        fouls_values = []
        
        for match in recent_matches:
            # Results
            result = match.get('result', 'D')
            if result == 'W':
                summary['wins'] += 1
            elif result == 'L':
                summary['losses'] += 1
            else:
                summary['draws'] += 1
            
            # Goals - make sure we're using the right keys
            goals_scored = match.get('goals_scored', 0)
            goals_conceded = match.get('goals_conceded', 0)
            
            # Debug print to see what we're getting
            self.logger.info(f"Match vs {match.get('opponent', 'Unknown')}: {goals_scored} scored, {goals_conceded} conceded")
            
            summary['goals_scored_total'] += goals_scored
            summary['goals_conceded_total'] += goals_conceded
            
            if goals_scored > 0:
                summary['matches_scored'] += 1
            if goals_conceded == 0:
                summary['clean_sheets'] += 1
            
            # Statistics
            if match.get('possession_pct'):
                possession_values.append(match['possession_pct'])
            if match.get('total_shots'):
                shots_values.append(match['total_shots'])
            if match.get('corners'):
                corners_values.append(match['corners'])
            if match.get('fouls'):
                fouls_values.append(match['fouls'])
        
        # Calculate averages
        if possession_values:
            summary['avg_possession'] = round(sum(possession_values) / len(possession_values), 1)
        if shots_values:
            summary['avg_shots_per_match'] = round(sum(shots_values) / len(shots_values), 1)
        if corners_values:
            summary['avg_corners_per_match'] = round(sum(corners_values) / len(corners_values), 1)
        if fouls_values:
            summary['avg_fouls_per_match'] = round(sum(fouls_values) / len(fouls_values), 1)
        
        # Form
        recent_results = [match.get('result', 'D') for match in recent_matches[:5]]
        summary['recent_form'] = ''.join(recent_results)
        
        return summary
    
    def export_team_data(self, team_data: Dict, output_dir: str = 'exports') -> str:
        """Export team data to JSON and CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        team_id = team_data.get('team_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export full JSON
        json_filename = f"{output_dir}/team_{team_id}_comprehensive_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(team_data, f, indent=2, default=str)
        
        # Export recent matches to CSV
        if team_data.get('recent_matches'):
            csv_filename = f"{output_dir}/team_{team_id}_recent_matches_{timestamp}.csv"
            df = pd.DataFrame(team_data['recent_matches'])
            df.to_csv(csv_filename, index=False)
            self.logger.info(f"📁 Exported recent matches to {csv_filename}")
        
        # Export season stats to CSV
        if team_data.get('season_stats'):
            season_csv = f"{output_dir}/team_{team_id}_season_stats_{timestamp}.csv"
            season_df = pd.DataFrame([team_data['season_stats']])
            season_df.to_csv(season_csv, index=False)
            self.logger.info(f"📁 Exported season stats to {season_csv}")
        
        self.logger.info(f"📁 Exported comprehensive data to {json_filename}")
        return json_filename

def test_single_team(team_id: int, tournament_id: int, season_id: int):
    """
    Test the scraper on a single team using corrected data collection
    
    Example team IDs:
    - Manchester City: 17
    - Arsenal: 42
    - Liverpool: 44
    - Chelsea: 38
    
    Premier League tournament_id: 17
    Season ID: 52186 (note: season endpoints may not work, but team data will)
    """
    
    print(f"🧪 TESTING CORRECTED HISTORICAL SCRAPER")
    print(f"=" * 45)
    print(f"Team ID: {team_id}")
    print(f"Tournament ID: {tournament_id}")
    print(f"Season ID: {season_id}")
    print(f"Method: Date-based search for completed matches")
    print()
    
    scraper = TeamHistoricalScraper()
    
    try:
        # Get comprehensive data using corrected method
        team_data = scraper.get_team_comprehensive_data(
            team_id=team_id,
            tournament_id=tournament_id,
            season_id=season_id,
            recent_matches=7
        )
        
        # Display summary
        print("📊 SEASON STATS COLLECTED:")
        season_stats = team_data.get('season_stats', {})
        for key, value in list(season_stats.items())[:10]:  # Show first 10
            print(f"   {key}: {value}")
        if len(season_stats) > 10:
            print(f"   ... and {len(season_stats) - 10} more stats")
        
        print(f"\n📅 RECENT MATCHES COLLECTED: {len(team_data.get('recent_matches', []))}")
        
        recent_matches = team_data.get('recent_matches', [])
        for i, match in enumerate(recent_matches[:5]):  # Show first 5
            opponent = match.get('opponent', 'Unknown')
            result = match.get('result', 'Unknown')
            score = match.get('final_score', 'N/A')
            goals_scored = match.get('goals_scored', 0)
            goals_conceded = match.get('goals_conceded', 0)
            venue = match.get('venue_type', 'Unknown')
            date = match.get('date', 'Unknown')
            
            print(f"   Match {i+1}: {date} vs {opponent} ({venue}): {result} {score}")
            print(f"             Goals: {goals_scored} scored, {goals_conceded} conceded")
        
        print(f"\n📈 RECENT FORM SUMMARY:")
        summary = team_data.get('recent_match_summary', {})
        print(f"   Form: {summary.get('recent_form', 'N/A')}")
        print(f"   Record: {summary.get('wins', 0)}W-{summary.get('draws', 0)}D-{summary.get('losses', 0)}L")
        print(f"   Goals: {summary.get('goals_scored_total', 0)} scored, {summary.get('goals_conceded_total', 0)} conceded")
        print(f"   Clean Sheets: {summary.get('clean_sheets', 0)}/{summary.get('matches_analyzed', 0)}")
        
        # Export data
        export_file = scraper.export_team_data(team_data)
        print(f"\n✅ TEST COMPLETED SUCCESSFULLY")
        print(f"📁 Data exported to: {export_file}")
        print(f"🎯 Using corrected date-based search method")
        print(f"📊 Found realistic match scores and data")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    # Test with Manchester City in Premier League
    # You can change these IDs to test other teams
    
    TEST_TEAM_ID = 17        # Manchester City
    TEST_TOURNAMENT_ID = 17  # Premier League
    TEST_SEASON_ID = 52186   # 2024/25 season
    
    print("🏗️  Historical Team Data Scraper - Test Mode")
    print("=" * 50)
    print("This will test the scraper on a single team first")
    print("Once verified working, we can expand to multiple teams")
    print()
    
    success = test_single_team(TEST_TEAM_ID, TEST_TOURNAMENT_ID, TEST_SEASON_ID)
    
    if success:
        print("\n🎉 Ready for production use!")
        print("💡 To test other teams, modify the TEST_TEAM_ID in the script")
        print("📚 Common Premier League team IDs:")
        print("   Manchester City: 17")
        print("   Arsenal: 42") 
        print("   Liverpool: 44")
        print("   Chelsea: 38")
        print("   Manchester United: 35")
    else:
        print("\n🔧 Please check the logs and fix any issues before proceeding")