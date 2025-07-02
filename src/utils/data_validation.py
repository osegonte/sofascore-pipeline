"""
Data validation utilities for ensuring data quality.
"""

from datetime import datetime
from typing import Any, Dict, List
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DataValidator:
    """Advanced data validation for SofaScore data."""
    
    @staticmethod
    def validate_match_id(match_id: Any) -> bool:
        """Validate match ID format."""
        try:
            id_int = int(match_id)
            return 1000 <= id_int <= 999999999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_team_name(name: Any) -> bool:
        """Validate team name."""
        if not isinstance(name, str):
            return False
        name = name.strip()
        return 1 <= len(name) <= 100 and not name.isdigit()
    
    @staticmethod
    def validate_score(score: Any) -> bool:
        """Validate match score."""
        try:
            score_int = int(score)
            return 0 <= score_int <= 50
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_minute(minute: Any) -> bool:
        """Validate match minute."""
        try:
            minute_int = int(minute)
            return 0 <= minute_int <= 150
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_coordinates(x: Any, y: Any) -> bool:
        """Validate field coordinates."""
        try:
            if x is None or y is None:
                return True
            x_float, y_float = float(x), float(y)
            return 0 <= x_float <= 100 and 0 <= y_float <= 100
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_possession(possession: Any) -> bool:
        """Validate possession percentage."""
        try:
            if possession is None:
                return True
            poss_float = float(possession)
            return 0 <= poss_float <= 100
        except (ValueError, TypeError):
            return False


class DataEnricher:
    """Enrich raw data with additional information and calculations."""
    
    @staticmethod
    def calculate_xg_simple(x: float, y: float, event_type: str) -> float:
        """Calculate a simple xG value based on position."""
        if event_type not in ['shot', 'goal']:
            return 0.0
        
        distance_from_goal = ((100 - x) ** 2 + (50 - y) ** 2) ** 0.5
        angle_factor = abs(50 - y) / 50
        
        base_xg = max(0.01, 0.8 - (distance_from_goal / 100))
        angle_adjusted_xg = base_xg * (1 - angle_factor * 0.3)
        
        if event_type == 'goal':
            return min(1.0, angle_adjusted_xg * 1.2)
        
        return min(0.99, angle_adjusted_xg)
    
    @staticmethod
    def enrich_event_data(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event data with calculated fields."""
        enriched = event_data.copy()
        
        # Calculate xG if coordinates are available
        if (event_data.get('x_coordinate') is not None and 
            event_data.get('y_coordinate') is not None and 
            event_data.get('event_type') in ['shot', 'goal']):
            
            xg = DataEnricher.calculate_xg_simple(
                event_data['x_coordinate'],
                event_data['y_coordinate'],
                event_data['event_type']
            )
            enriched['calculated_xg'] = round(xg, 3)
        
        # Add time period classification
        minute = event_data.get('minute', 0)
        if minute <= 15:
            enriched['time_period'] = 'early'
        elif minute <= 30:
            enriched['time_period'] = 'first_half_mid'
        elif minute <= 45:
            enriched['time_period'] = 'first_half_late'
        elif minute <= 60:
            enriched['time_period'] = 'second_half_early'
        elif minute <= 75:
            enriched['time_period'] = 'second_half_mid'
        elif minute <= 90:
            enriched['time_period'] = 'second_half_late'
        else:
            enriched['time_period'] = 'extra_time'
        
        return enriched
