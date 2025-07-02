"""
Simple data processing utilities without pandas dependency.
Alternative for Python 3.13 until pandas 2.2+ is available.
"""

import json
import csv
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from collections import defaultdict, Counter
import statistics


class SimpleDataFrame:
    """A lightweight DataFrame-like class for basic data operations."""
    
    def __init__(self, data: Union[List[Dict], List[List]], columns: Optional[List[str]] = None):
        """Initialize with data and optional column names."""
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                # Data is list of dictionaries
                self.columns = list(data[0].keys()) if data else []
                self.data = [list(row.values()) for row in data]
            elif isinstance(data[0], list):
                # Data is list of lists
                self.columns = columns or [f"col_{i}" for i in range(len(data[0]))]
                self.data = data
            else:
                raise ValueError("Data must be list of dictionaries or list of lists")
        else:
            self.columns = columns or []
            self.data = []
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, key):
        """Get column by name or row by index."""
        if isinstance(key, str):
            # Get column
            if key not in self.columns:
                raise KeyError(f"Column '{key}' not found")
            col_idx = self.columns.index(key)
            return [row[col_idx] for row in self.data]
        elif isinstance(key, int):
            # Get row
            return dict(zip(self.columns, self.data[key]))
        else:
            raise TypeError("Key must be string (column name) or int (row index)")
    
    def head(self, n: int = 5) -> List[Dict]:
        """Get first n rows as dictionaries."""
        return [dict(zip(self.columns, row)) for row in self.data[:n]]
    
    def tail(self, n: int = 5) -> List[Dict]:
        """Get last n rows as dictionaries."""
        return [dict(zip(self.columns, row)) for row in self.data[-n:]]
    
    def filter(self, condition: Callable[[Dict], bool]) -> 'SimpleDataFrame':
        """Filter rows based on condition function."""
        filtered_data = []
        for row in self.data:
            row_dict = dict(zip(self.columns, row))
            if condition(row_dict):
                filtered_data.append(row)
        return SimpleDataFrame(filtered_data, self.columns)
    
    def sort(self, column: str, reverse: bool = False) -> 'SimpleDataFrame':
        """Sort by column."""
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        
        col_idx = self.columns.index(column)
        sorted_data = sorted(self.data, key=lambda row: row[col_idx], reverse=reverse)
        return SimpleDataFrame(sorted_data, self.columns)
    
    def group_by(self, column: str) -> Dict[Any, 'SimpleDataFrame']:
        """Group by column values."""
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        
        col_idx = self.columns.index(column)
        groups = defaultdict(list)
        
        for row in self.data:
            group_key = row[col_idx]
            groups[group_key].append(row)
        
        return {key: SimpleDataFrame(rows, self.columns) for key, rows in groups.items()}
    
    def aggregate(self, column: str, func: str) -> Any:
        """Aggregate column using function (sum, mean, count, min, max)."""
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")
        
        col_data = self[column]
        
        if func == 'count':
            return len(col_data)
        elif func == 'sum':
            return sum(x for x in col_data if x is not None)
        elif func == 'mean':
            numeric_data = [x for x in col_data if isinstance(x, (int, float))]
            return statistics.mean(numeric_data) if numeric_data else 0
        elif func == 'min':
            return min(x for x in col_data if x is not None)
        elif func == 'max':
            return max(x for x in col_data if x is not None)
        else:
            raise ValueError(f"Unknown aggregation function: {func}")
    
    def to_dict(self) -> List[Dict]:
        """Convert to list of dictionaries."""
        return [dict(zip(self.columns, row)) for row in self.data]
    
    def to_csv(self, filename: str):
        """Export to CSV file."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            writer.writerows(self.data)


class JSONProcessor:
    """Process JSON data from SofaScore API responses."""
    
    @staticmethod
    def extract_match_info(match_data: Dict) -> Dict:
        """Extract basic match information from feed data."""
        try:
            return {
                'match_id': match_data.get('id'),
                'home_team': match_data.get('homeTeam', {}).get('name'),
                'away_team': match_data.get('awayTeam', {}).get('name'),
                'home_score': match_data.get('homeScore', {}).get('current'),
                'away_score': match_data.get('awayScore', {}).get('current'),
                'status': match_data.get('status', {}).get('description'),
                'minute': match_data.get('time', {}).get('currentPeriodStartTimestamp'),
                'competition': match_data.get('tournament', {}).get('name'),
                'date': match_data.get('startTimestamp')
            }
        except Exception as e:
            return {'error': f"Failed to extract match info: {e}"}
    
    @staticmethod
    def extract_events(events_data: Dict) -> List[Dict]:
        """Extract events from incidents data."""
        try:
            incidents = events_data.get('incidents', [])
            events = []
            
            for incident in incidents:
                event = {
                    'minute': incident.get('time'),
                    'type': incident.get('incidentType'),
                    'team': incident.get('homeScore') is not None,  # True if home team
                    'player': incident.get('player', {}).get('name') if incident.get('player') else None,
                    'description': incident.get('text'),
                    'x': incident.get('x'),
                    'y': incident.get('y')
                }
                events.append(event)
            
            return events
        except Exception as e:
            return [{'error': f"Failed to extract events: {e}"}]
    
    @staticmethod
    def extract_statistics(stats_data: Dict) -> Dict:
        """Extract match statistics."""
        try:
            stats = stats_data.get('statistics', [])
            extracted = {}
            
            for period in stats:
                period_name = period.get('period', 'unknown')
                groups = period.get('groups', [])
                
                for group in groups:
                    group_name = group.get('groupName', 'unknown')
                    stat_items = group.get('statisticsItems', [])
                    
                    for item in stat_items:
                        stat_name = item.get('name', 'unknown')
                        home_value = item.get('home')
                        away_value = item.get('away')
                        
                        key = f"{period_name}_{group_name}_{stat_name}".lower().replace(' ', '_')
                        extracted[f"{key}_home"] = home_value
                        extracted[f"{key}_away"] = away_value
            
            return extracted
        except Exception as e:
            return {'error': f"Failed to extract statistics: {e}"}


class MatchAnalyzer:
    """Analyze match data for insights."""
    
    def __init__(self):
        self.matches = []
        self.events = []
        self.stats = []
    
    def add_match_data(self, match_data: Dict, events_data: Dict, stats_data: Dict):
        """Add match data for analysis."""
        match_info = JSONProcessor.extract_match_info(match_data)
        events = JSONProcessor.extract_events(events_data)
        stats = JSONProcessor.extract_statistics(stats_data)
        
        self.matches.append(match_info)
        self.events.extend(events)
        self.stats.append(stats)
    
    def get_goal_times(self) -> List[int]:
        """Get all goal times across matches."""
        goal_times = []
        for event in self.events:
            if event.get('type') == 'goal' and event.get('minute'):
                goal_times.append(event['minute'])
        return sorted(goal_times)
    
    def get_goal_distribution(self, interval: int = 15) -> Dict[str, int]:
        """Get goal distribution by time intervals."""
        goal_times = self.get_goal_times()
        distribution = defaultdict(int)
        
        for minute in goal_times:
            interval_start = (minute // interval) * interval
            interval_end = interval_start + interval
            interval_key = f"{interval_start}-{interval_end}"
            distribution[interval_key] += 1
        
        return dict(distribution)
    
    def get_team_stats(self) -> Dict[str, Dict]:
        """Get aggregated team statistics."""
        team_stats = defaultdict(lambda: {
            'matches': 0,
            'goals_for': 0,
            'goals_against': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0
        })
        
        for match in self.matches:
            if 'error' in match:
                continue
                
            home_team = match.get('home_team')
            away_team = match.get('away_team')
            home_score = match.get('home_score', 0) or 0
            away_score = match.get('away_score', 0) or 0
            
            if home_team and away_team:
                # Home team stats
                team_stats[home_team]['matches'] += 1
                team_stats[home_team]['goals_for'] += home_score
                team_stats[home_team]['goals_against'] += away_score
                
                # Away team stats
                team_stats[away_team]['matches'] += 1
                team_stats[away_team]['goals_for'] += away_score
                team_stats[away_team]['goals_against'] += home_score
                
                # Results
                if home_score > away_score:
                    team_stats[home_team]['wins'] += 1
                    team_stats[away_team]['losses'] += 1
                elif home_score < away_score:
                    team_stats[home_team]['losses'] += 1
                    team_stats[away_team]['wins'] += 1
                else:
                    team_stats[home_team]['draws'] += 1
                    team_stats[away_team]['draws'] += 1
        
        return dict(team_stats)


class SimpleCSVExporter:
    """Export data to CSV format."""
    
    @staticmethod
    def export_matches(matches: List[Dict], filename: str):
        """Export match data to CSV."""
        if not matches:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)
    
    @staticmethod
    def export_events(events: List[Dict], filename: str):
        """Export events data to CSV."""
        if not events:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=events[0].keys())
            writer.writeheader()
            writer.writerows(events)
    
    @staticmethod
    def export_team_stats(team_stats: Dict, filename: str):
        """Export team statistics to CSV."""
        if not team_stats:
            return
        
        rows = []
        for team, stats in team_stats.items():
            row = {'team': team}
            row.update(stats)
            rows.append(row)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)


# Utility functions for common operations
def calculate_xg_features(events: List[Dict]) -> Dict[str, float]:
    """Calculate xG-based features from events."""
    total_xg = 0
    shot_count = 0
    big_chances = 0
    
    for event in events:
        if event.get('type') in ['shot', 'goal']:
            shot_count += 1
            # Simulate xG calculation (replace with actual xG data when available)
            if event.get('x') and event.get('y'):
                # Simple distance-based xG approximation
                x, y = event['x'], event['y']
                distance_from_goal = ((100 - x) ** 2 + (50 - y) ** 2) ** 0.5
                xg = max(0.02, 0.5 - (distance_from_goal / 100))
                total_xg += xg
                
                if xg > 0.3:
                    big_chances += 1
    
    return {
        'total_xg': round(total_xg, 3),
        'shots': shot_count,
        'big_chances': big_chances,
        'xg_per_shot': round(total_xg / max(shot_count, 1), 3)
    }


def rolling_average(data: List[float], window: int) -> List[float]:
    """Calculate rolling average."""
    if len(data) < window:
        return data
    
    result = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(data[i])
        else:
            window_data = data[i - window + 1:i + 1]
            result.append(sum(window_data) / len(window_data))
    
    return result


def get_time_since_last_goal(events: List[Dict], current_minute: int) -> int:
    """Get minutes since last goal."""
    goal_times = [
        event['minute'] for event in events
        if event.get('type') == 'goal' and event.get('minute', 0) <= current_minute
    ]
    
    if not goal_times:
        return current_minute
    
    return current_minute - max(goal_times)


# Example usage and testing
if __name__ == "__main__":
    # Test SimpleDataFrame
    sample_data = [
        {'team': 'Arsenal', 'goals': 3, 'shots': 12},
        {'team': 'Chelsea', 'goals': 1, 'shots': 8},
        {'team': 'Arsenal', 'goals': 2, 'shots': 15},
        {'team': 'Chelsea', 'goals': 0, 'shots': 6},
    ]
    
    df = SimpleDataFrame(sample_data)
    print("Sample DataFrame:")
    print(df.head())
    
    print("\nFiltered (goals > 1):")
    filtered = df.filter(lambda row: row['goals'] > 1)
    print(filtered.head())
    
    print("\nGrouped by team:")
    groups = df.group_by('team')
    for team, group_df in groups.items():
        avg_goals = group_df.aggregate('goals', 'mean')
        print(f"{team}: {avg_goals:.1f} avg goals")