#!/usr/bin/env python3
"""
Stage 8: Dashboard Backend Integration
Connects the web dashboard with Stage 7 real-time analysis system
"""

import json
import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stage8_backend")

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️  FastAPI not available. Installing...")
    os.system("pip install fastapi uvicorn websockets --quiet")
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, HTMLResponse
    import uvicorn
    FASTAPI_AVAILABLE = True

@dataclass
class MatchData:
    """Live match data structure"""
    match_id: int
    minute: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    probabilities: Dict[str, float]
    confidence: float
    recommendation: Dict[str, str]
    last_updated: str

@dataclass
class AlertData:
    """Alert data structure"""
    alert_id: str
    match_id: int
    message: str
    probability: float
    confidence: float
    teams: str
    timestamp: str
    priority: str = "high"

class Stage8Backend:
    """Backend service for Stage 8 dashboard"""
    
    def __init__(self):
        self.stage7_data_dir = Path("stage7/data/realtime")
        self.app = FastAPI(title="Stage 8 Dashboard API", version="1.0.0")
        self.websocket_connections = []
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def serve_dashboard():
            """Serve the main dashboard"""
            # Create a simple dashboard HTML if the full one isn't available
            dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SofaScore Betting Dashboard - Stage 8</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
            color: #ffffff;
            margin: 0;
            padding: 2rem;
            min-height: 100vh;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .status-card {
            background: rgba(26, 35, 50, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        .matches-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
        }
        .match-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
        }
        .bet-signal {
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            margin-top: 1rem;
        }
        .bet-signal.buy {
            background: linear-gradient(135deg, #2ed573, #17c0eb);
            color: #000;
        }
        .bet-signal.consider {
            background: linear-gradient(135deg, #ffa502, #ff6348);
            color: #000;
        }
        .bet-signal.hold {
            background: rgba(255, 255, 255, 0.1);
            color: #888;
        }
        .probability-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        .probability-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff4757 0%, #ffa502 50%, #2ed573 100%);
            transition: width 0.5s ease;
        }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .loading {
            text-align: center;
            padding: 2rem;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">⚽ SofaScore Betting Dashboard</div>
            <p>Stage 8: Real-Time Analysis & Betting Recommendations</p>
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
        </div>
        
        <div class="status-card">
            <h2>System Status</h2>
            <div id="system-status">
                <div class="loading">📡 Loading system status...</div>
            </div>
        </div>
        
        <div class="status-card">
            <h2>🔴 Live Matches & Predictions</h2>
            <div id="matches-container">
                <div class="loading">📊 Loading live matches...</div>
            </div>
        </div>
        
        <div class="status-card">
            <h2>🚨 High Confidence Alerts</h2>
            <div id="alerts-container">
                <div class="loading">⚠️ Loading alerts...</div>
            </div>
        </div>
    </div>

    <script>
        let lastUpdate = null;
        
        async function loadData() {
            try {
                // Load system status
                const statusResponse = await fetch('/api/system-status');
                const statusData = await statusResponse.json();
                updateSystemStatus(statusData);
                
                // Load live matches
                const matchesResponse = await fetch('/api/live-matches');
                const matchesData = await matchesResponse.json();
                updateMatches(matchesData.matches || []);
                
                // Load alerts
                const alertsResponse = await fetch('/api/alerts');
                const alertsData = await alertsResponse.json();
                updateAlerts(alertsData.alerts || []);
                
                lastUpdate = new Date();
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('matches-container').innerHTML = 
                    '<div style="color: #ff4757;">❌ Error loading data. Check if Stage 7 is running.</div>';
            }
        }
        
        function updateSystemStatus(status) {
            const container = document.getElementById('system-status');
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <strong>Stage 7:</strong> ${status.stage7_active ? '✅ Running' : '❌ Not Running'}
                    </div>
                    <div>
                        <strong>Processes:</strong> ${status.processes_running}
                    </div>
                    <div>
                        <strong>Data Freshness:</strong> ${status.data_freshness || 'Unknown'}
                    </div>
                    <div>
                        <strong>Last Update:</strong> ${lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
                    </div>
                </div>
            `;
        }
        
        function updateMatches(matches) {
            const container = document.getElementById('matches-container');
            
            if (matches.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: #888;">
                        <div style="font-size: 2rem; margin-bottom: 1rem;">⚽</div>
                        <h3>No Live Matches</h3>
                        <p>Waiting for matches in late stages (55+ minutes)</p>
                        <small>Stage 7 monitors live matches and provides data here</small>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = `
                <div class="matches-grid">
                    ${matches.map(match => `
                        <div class="match-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                <div style="font-size: 1.2rem; font-weight: bold;">
                                    ${match.home_team} ${match.home_score} - ${match.away_score} ${match.away_team}
                                </div>
                                <div style="color: #00ff88; font-weight: bold;">
                                    ${match.minute}'
                                </div>
                            </div>
                            
                            <div style="margin: 1rem 0;">
                                <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Goal Probability (15 min)</div>
                                <div style="font-size: 1.5rem; font-weight: bold; color: ${getProbabilityColor(match.probabilities.goal_next_15min)};">
                                    ${Math.round(match.probabilities.goal_next_15min * 100)}%
                                </div>
                                <div class="probability-bar">
                                    <div class="probability-fill" style="width: ${match.probabilities.goal_next_15min * 100}%"></div>
                                </div>
                            </div>
                            
                            <div style="font-size: 0.9rem; margin-bottom: 1rem;">
                                <strong>Confidence:</strong> ${Math.round(match.confidence * 100)}%
                            </div>
                            
                            <div class="bet-signal ${match.recommendation.action.toLowerCase()}">
                                ${getRecommendationText(match.recommendation.action)}
                                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.8;">
                                    ${match.recommendation.reason}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            
            if (alerts.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: #888;">
                        <div style="font-size: 2rem; margin-bottom: 1rem;">🔕</div>
                        <p>No active alerts</p>
                        <small>High-confidence betting opportunities will appear here</small>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = alerts.map(alert => `
                <div style="background: rgba(255, 87, 87, 0.1); border: 1px solid #ff5757; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="font-weight: bold; margin-bottom: 0.5rem;">
                        🚨 ${alert.message}
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        ${alert.teams}
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #888;">
                        <span>Probability: ${Math.round(alert.probability * 100)}%</span>
                        <span>Confidence: ${Math.round(alert.confidence * 100)}%</span>
                    </div>
                </div>
            `).join('');
        }
        
        function getProbabilityColor(probability) {
            if (probability >= 0.7) return '#2ed573';
            if (probability >= 0.5) return '#ffa502';
            if (probability >= 0.3) return '#ff6348';
            return '#ff4757';
        }
        
        function getRecommendationText(action) {
            switch (action) {
                case 'BET': return '🎯 STRONG BUY';
                case 'CONSIDER': return '🤔 CONSIDER';
                case 'HOLD': return '✋ HOLD';
                default: return action;
            }
        }
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', loadData);
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
        
        console.log('🚀 Stage 8 Dashboard loaded!');
        console.log('📊 Dashboard URL: http://localhost:8008');
        console.log('📚 API Documentation: http://localhost:8008/docs');
    </script>
</body>
</html>
            """
            return HTMLResponse(content=dashboard_html)
        
        @self.app.get("/api/live-matches")
        async def get_live_matches():
            """Get current live matches from Stage 7"""
            try:
                matches = await self.load_live_matches()
                return {"matches": matches, "count": len(matches)}
            except Exception as e:
                logger.error(f"Error loading live matches: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get current alerts from Stage 7"""
            try:
                alerts = await self.load_alerts()
                return {"alerts": alerts, "count": len(alerts)}
            except Exception as e:
                logger.error(f"Error loading alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/predictions/{match_id}")
        async def get_match_predictions(match_id: int):
            """Get detailed predictions for a specific match"""
            try:
                prediction = await self.load_match_prediction(match_id)
                if not prediction:
                    raise HTTPException(status_code=404, detail="Match not found")
                return prediction
            except Exception as e:
                logger.error(f"Error loading prediction for match {match_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/system-status")
        async def get_system_status():
            """Get Stage 7 system status"""
            try:
                status = await self.check_stage7_status()
                return status
            except Exception as e:
                logger.error(f"Error checking system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def load_live_matches(self) -> List[MatchData]:
        """Load live matches from Stage 7 data"""
        live_matches_file = self.stage7_data_dir / "live_matches.json"
        
        if not live_matches_file.exists():
            logger.warning("No live matches file found - returning demo data")
            # Return demo data if no real data available
            return [
                MatchData(
                    match_id=12345,
                    minute=65,
                    home_team="Arsenal",
                    away_team="Chelsea",
                    home_score=1,
                    away_score=0,
                    probabilities={
                        "goal_next_1min": 0.12,
                        "goal_next_5min": 0.34,
                        "goal_next_15min": 0.58
                    },
                    confidence=0.78,
                    recommendation={
                        "action": "BET",
                        "reason": "High confidence betting opportunity"
                    },
                    last_updated=datetime.now().isoformat()
                ),
                MatchData(
                    match_id=12346,
                    minute=72,
                    home_team="Liverpool",
                    away_team="Man City",
                    home_score=2,
                    away_score=1,
                    probabilities={
                        "goal_next_1min": 0.08,
                        "goal_next_5min": 0.25,
                        "goal_next_15min": 0.45
                    },
                    confidence=0.62,
                    recommendation={
                        "action": "CONSIDER",
                        "reason": "Medium confidence opportunity"
                    },
                    last_updated=datetime.now().isoformat()
                )
            ]
        
        try:
            with open(live_matches_file, 'r') as f:
                raw_matches = json.load(f)
            
            matches = []
            for match_data in raw_matches:
                # Load corresponding predictions
                prediction = await self.load_match_prediction(match_data['match_id'])
                
                if prediction:
                    match = MatchData(
                        match_id=match_data['match_id'],
                        minute=match_data.get('minute', 0),
                        home_team=match_data.get('home_team', 'Team A'),
                        away_team=match_data.get('away_team', 'Team B'),
                        home_score=match_data.get('home_score', 0),
                        away_score=match_data.get('away_score', 0),
                        probabilities=prediction.get('ensemble_probabilities', {}),
                        confidence=prediction.get('confidence_score', 0.0),
                        recommendation=prediction.get('recommendation', {
                            'action': 'HOLD',
                            'reason': 'No recommendation available'
                        }),
                        last_updated=match_data.get('last_update', datetime.now().isoformat())
                    )
                    matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error loading live matches: {e}")
            return []
    
    async def load_match_prediction(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Load the latest prediction for a specific match"""
        predictions_dir = self.stage7_data_dir / "ensemble_predictions"
        
        if not predictions_dir.exists():
            return None
        
        # Find the latest prediction file for this match
        prediction_files = list(predictions_dir.glob(f"match_{match_id}_*.json"))
        
        if not prediction_files:
            return None
        
        # Get the most recent prediction
        latest_file = max(prediction_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading prediction file {latest_file}: {e}")
            return None
    
    async def load_alerts(self) -> List[AlertData]:
        """Load active alerts from Stage 7"""
        alerts_dir = self.stage7_data_dir / "alerts"
        
        if not alerts_dir.exists():
            # Return demo alert if no real alerts
            return [
                AlertData(
                    alert_id="demo_alert_1",
                    match_id=12345,
                    message="HIGH CONFIDENCE BETTING OPPORTUNITY",
                    probability=0.58,
                    confidence=0.78,
                    teams="Arsenal vs Chelsea",
                    timestamp=datetime.now().isoformat(),
                    priority="high"
                )
            ]
        
        alerts = []
        
        # Get all alert files from the last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for alert_file in alerts_dir.glob("alert_*.json"):
            file_time = datetime.fromtimestamp(alert_file.stat().st_mtime)
            
            if file_time > cutoff_time:
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    alert = AlertData(
                        alert_id=alert_data.get('alert_id', str(alert_file.stem)),
                        match_id=alert_data.get('match_id', 0),
                        message=alert_data.get('message', 'Alert'),
                        probability=alert_data.get('probability', 0.0),
                        confidence=alert_data.get('confidence', 0.0),
                        teams=f"Match {alert_data.get('match_id', 'Unknown')}",
                        timestamp=alert_data.get('timestamp', file_time.isoformat()),
                        priority=alert_data.get('priority', 'high')
                    )
                    alerts.append(alert)
                    
                except Exception as e:
                    logger.error(f"Error loading alert file {alert_file}: {e}")
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    async def check_stage7_status(self) -> Dict[str, Any]:
        """Check if Stage 7 is running and get system status"""
        status = {
            "stage7_active": False,
            "processes_running": 0,
            "last_data_update": None,
            "data_freshness": "unknown"
        }
        
        # Check if Stage 7 PID files exist
        stage7_pids_dir = Path("stage7/pids")
        if stage7_pids_dir.exists():
            pid_files = list(stage7_pids_dir.glob("*.pid"))
            status["processes_running"] = len(pid_files)
            status["stage7_active"] = len(pid_files) > 0
        
        # Check data freshness
        live_matches_file = self.stage7_data_dir / "live_matches.json"
        if live_matches_file.exists():
            last_modified = datetime.fromtimestamp(live_matches_file.stat().st_mtime)
            status["last_data_update"] = last_modified.isoformat()
            
            age_seconds = (datetime.now() - last_modified).total_seconds()
            if age_seconds < 60:
                status["data_freshness"] = "fresh"
            elif age_seconds < 300:
                status["data_freshness"] = "recent"
            else:
                status["data_freshness"] = "stale"
        
        return status
    
    def run(self, host: str = "0.0.0.0", port: int = 8008):
        """Run the Stage 8 backend server"""
        logger.info(f"Starting Stage 8 Dashboard Backend on {host}:{port}")
        logger.info(f"Dashboard URL: http://{host}:{port}")
        logger.info(f"API Documentation: http://{host}:{port}/docs")
        
        uvicorn.run(self.app, host=host, port=port, log_level="info")

async def main():
    """Main entry point for Stage 8 backend"""
    
    # Create and run backend
    backend = Stage8Backend()
    
    # Check if Stage 7 is available
    stage7_status = await backend.check_stage7_status()
    if not stage7_status["stage7_active"]:
        logger.warning("Stage 7 appears to be inactive. Start Stage 7 first with: ./stage7.sh start")
    else:
        logger.info(f"Stage 7 is active with {stage7_status['processes_running']} processes")
    
    # Start the backend server
    backend.run()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Test mode - check Stage 7 integration
            backend = Stage8Backend()
            
            async def test_integration():
                logger.info("Testing Stage 8 integration with Stage 7...")
                
                # Test live matches loading
                matches = await backend.load_live_matches()
                logger.info(f"Found {len(matches)} live matches")
                
                # Test alerts loading
                alerts = await backend.load_alerts()
                logger.info(f"Found {len(alerts)} active alerts")
                
                # Test system status
                status = await backend.check_stage7_status()
                logger.info(f"Stage 7 status: {status}")
                
                logger.info("✅ Stage 8 integration test completed")
            
            asyncio.run(test_integration())
        
        elif sys.argv[1] == "setup":
            # Setup mode - create directories and config
            stage8_dir = Path("stage8")
            stage8_dir.mkdir(exist_ok=True)
            
            subdirs = ["logs", "exports", "static", "templates"]
            for subdir in subdirs:
                (stage8_dir / subdir).mkdir(exist_ok=True)
            
            config = {
                "stage8": {
                    "dashboard_host": "0.0.0.0",
                    "dashboard_port": 8008,
                    "update_interval": 30,
                    "websocket_enabled": True,
                    "auto_refresh": True
                }
            }
            
            config_file = stage8_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Stage 8 setup completed. Config saved to: {config_file}")
            logger.info("Run with: python stage8_backend.py")
        
    else:
        # Normal mode - run the server
        asyncio.run(main())
