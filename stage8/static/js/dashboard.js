// Stage 8 Dashboard JavaScript
// Real-time dashboard functionality

class Stage8Dashboard {
    constructor() {
        this.wsUrl = `ws://${window.location.host}/ws`;
        this.websocket = null;
        this.retryCount = 0;
        this.maxRetries = 5;
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    connectWebSocket() {
        try {
            this.websocket = new WebSocket(this.wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔗 WebSocket connected');
                this.retryCount = 0;
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.retryWebSocketConnection();
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.retryWebSocketConnection();
        }
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'update') {
            this.updateDashboard(data);
        }
    }
    
    async loadInitialData() {
        try {
            const [matchesResponse, alertsResponse] = await Promise.all([
                fetch('/api/live-matches'),
                fetch('/api/alerts')
            ]);
            
            const matchesData = await matchesResponse.json();
            const alertsData = await alertsResponse.json();
            
            this.renderMatches(matchesData.matches);
            this.renderAlerts(alertsData.alerts);
            
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = connected ? 'status-connected' : 'status-disconnected';
        }
    }
    
    retryWebSocketConnection() {
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            console.log(`🔄 Retrying WebSocket connection (${this.retryCount}/${this.maxRetries})`);
            setTimeout(() => this.connectWebSocket(), 5000);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.stage8Dashboard = new Stage8Dashboard();
});
