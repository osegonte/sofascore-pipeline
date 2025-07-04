#!/usr/bin/env python3
"""
Stage 7 Integration for Stage 8 Dashboard
Monitors Stage 7 outputs and provides data to dashboard
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Stage7Integration:
    """Integration layer between Stage 7 and Stage 8"""
    
    def __init__(self):
        self.stage7_data_dir = Path("stage7/data/realtime")
        self.last_check = None
        
    async def check_stage7_status(self):
        """Check if Stage 7 is running"""
        pid_dir = Path("stage7/pids")
        if not pid_dir.exists():
            return False
        
        pid_files = list(pid_dir.glob("*.pid"))
        return len(pid_files) > 0
    
    async def get_live_data(self):
        """Get the latest data from Stage 7"""
        if not await self.check_stage7_status():
            logger.warning("Stage 7 not running")
            return None
        
        try:
            # Read live matches
            live_matches_file = self.stage7_data_dir / "live_matches.json"
            if live_matches_file.exists():
                with open(live_matches_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading Stage 7 data: {e}")
        
        return None

if __name__ == "__main__":
    integration = Stage7Integration()
    
    async def test():
        status = await integration.check_stage7_status()
        print(f"Stage 7 Status: {'Running' if status else 'Not Running'}")
        
        data = await integration.get_live_data()
        if data:
            print(f"Found {len(data)} live matches")
        else:
            print("No live data available")
    
    asyncio.run(test())
