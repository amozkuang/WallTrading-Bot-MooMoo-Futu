"""
Simple Web Dashboard for Trading Bot Monitoring
Version 2.0 - 09/03/2026

Monitors bot status, pending trades, and order history
Access at: http://localhost:5000
"""

from flask import Flask, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# File paths
ORDER_HISTORY_FILE = "order_history.json"
LOG_FILE = "logs.log"

# HTML template embedded directly
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .card h2 {
            color: #333;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            opacity: 0.7;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #888;
            font-size: 0.9em;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4caf50;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .execution-schedule {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }

        .execution-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }

        .execution-item:last-child {
            border-bottom: none;
        }

        .execution-time {
            font-weight: bold;
            color: #333;
        }

        .execution-desc {
            color: #888;
            font-size: 0.9em;
        }

        .trades-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .trade-stat {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }

        .trade-stat .number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }

        .trade-stat .label {
            color: #888;
            font-size: 0.85em;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .logs-container {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .logs-container h2 {
            color: #333;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            opacity: 0.7;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .log-entry {
            background: #f9f9f9;
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #667eea;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #333;
            overflow-x: auto;
            word-break: break-all;
        }

        .log-entry.buy {
            border-left-color: #4caf50;
            background: #f1f8f4;
        }

        .log-entry.sell {
            border-left-color: #ff6b6b;
            background: #fff1f1;
        }

        .log-entry.error {
            border-left-color: #ff6b6b;
            background: #fff1f1;
        }

        .log-entry.info {
            border-left-color: #2196f3;
            background: #f0f8ff;
        }

        .footer {
            text-align: center;
            color: white;
            font-size: 0.9em;
            margin-top: 40px;
        }

        .loading {
            color: #888;
            font-style: italic;
        }

        .config-box {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 0.9em;
        }

        .config-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }

        .config-item:last-child {
            border-bottom: none;
        }

        .label {
            color: #888;
            font-weight: 500;
        }

        .value {
            color: #333;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Trading Bot Dashboard</h1>
            <p>Real-time monitoring of your automated trading strategy</p>
        </div>

        <!-- Status Cards -->
        <div class="grid">
            <!-- Bot Status -->
            <div class="card">
                <h2>🤖 Bot Status</h2>
                <div class="stat-value">
                    <span class="status-indicator"></span>
                    <span id="status-text">Loading...</span>
                </div>
                <div class="stat-label" id="status-time">Last updated: --</div>
            </div>

            <!-- Trading Stats -->
            <div class="card">
                <h2>📊 Trading Stats</h2>
                <div class="stat-value" id="total-trades">0</div>
                <div class="stat-label">Total Trades</div>
                <div class="trades-section">
                    <div class="trade-stat">
                        <div class="number" id="buy-count">0</div>
                        <div class="label">Buy</div>
                    </div>
                    <div class="trade-stat">
                        <div class="number" id="sell-count">0</div>
                        <div class="label">Sell</div>
                    </div>
                </div>
            </div>

            <!-- Execution Schedule -->
            <div class="card">
                <h2>⏰ Execution Schedule</h2>
                <div class="execution-schedule">
                    <div class="execution-item">
                        <div>
                            <div class="execution-time">📅 Every Monday</div>
                            <div class="execution-desc">8:00 PM SG Time</div>
                        </div>
                    </div>
                    <div class="execution-item">
                        <div>
                            <div class="execution-time">📅 Every Friday</div>
                            <div class="execution-desc">8:00 AM SG Time</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Configuration -->
            <div class="card">
                <h2>⚙️ Configuration</h2>
                <div class="config-box">
                    <div class="config-item">
                        <span class="label">Mode:</span>
                        <span class="value">Paper Trading</span>
                    </div>
                    <div class="config-item">
                        <span class="label">Capital:</span>
                        <span class="value">$1,000</span>
                    </div>
                    <div class="config-item">
                        <span class="label">Max Positions:</span>
                        <span class="value">4</span>
                    </div>
                    <div class="config-item">
                        <span class="label">Stocks:</span>
                        <span class="value">9</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Logs -->
        <div class="logs-container">
            <h2>📝 Recent Activity Logs</h2>
            <div id="logs-list">
                <div class="loading">Loading logs...</div>
            </div>
        </div>

        <div class="footer">
            <p>🚀 Trading Bot v3.1 | Monitoring Dashboard</p>
            <p id="last-update">Last updated: --</p>
        </div>
    </div>

    <script>
        // Refresh interval (5 seconds)
        const REFRESH_INTERVAL = 5000;

        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('status-text').textContent = data.status;
                document.getElementById('status-time').textContent = `Last execution: ${data.last_execution || 'Waiting for first run'}`;
                document.getElementById('total-trades').textContent = data.total_trades;
                document.getElementById('buy-count').textContent = data.buy_orders;
                document.getElementById('sell-count').textContent = data.sell_orders;
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }

        async function fetchLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                const logsList = document.getElementById('logs-list');
                
                if (data.logs.length === 0) {
                    logsList.innerHTML = '<div class="loading">No logs yet...</div>';
                    return;
                }

                logsList.innerHTML = data.logs.reverse().map(log => {
                    let className = 'log-entry';
                    if (log.includes('BUY')) className += ' buy';
                    else if (log.includes('SELL')) className += ' sell';
                    else if (log.includes('Error') || log.includes('failed')) className += ' error';
                    else if (log.includes('Strategy') || log.includes('Execution')) className += ' info';
                    
                    return `<div class="${className}">${escapeHtml(log)}</div>`;
                }).join('');
            } catch (error) {
                console.error('Error fetching logs:', error);
            }
        }

        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }

        function updateTimestamp() {
            const now = new Date();
            document.getElementById('last-update').textContent = 
                `Last updated: ${now.toLocaleString()}`;
        }

        // Initial load
        fetchStatus();
        fetchLogs();
        updateTimestamp();

        // Auto-refresh
        setInterval(() => {
            fetchStatus();
            fetchLogs();
            updateTimestamp();
        }, REFRESH_INTERVAL);

        console.log('Dashboard loaded. Refreshing every', REFRESH_INTERVAL / 1000, 'seconds');
    </script>
</body>
</html>'''


def read_order_history():
    """Read order history from JSON file"""
    if os.path.exists(ORDER_HISTORY_FILE):
        try:
            with open(ORDER_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def read_logs():
    """Read recent logs"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-100:]]  # Last 100 lines
        except:
            return []
    return []


def get_bot_status():
    """Get current bot status"""
    orders = read_order_history()
    logs = read_logs()
    
    # Count trades
    buy_count = sum(1 for o in orders if 'BUY' in str(o).upper())
    sell_count = sum(1 for o in orders if 'SELL' in str(o).upper())
    
    # Get last execution time from logs
    last_execution = "Waiting for next execution"
    for log in reversed(logs):
        if "Strategy Decision running" in log or "Execution Time" in log:
            last_execution = log
            break
    
    return {
        "status": "🟢 Running",
        "total_trades": len(orders),
        "buy_orders": buy_count,
        "sell_orders": sell_count,
        "last_execution": last_execution,
        "timestamp": datetime.now().isoformat()
    }


@app.route('/')
def dashboard():
    """Main dashboard page"""
    return HTML_TEMPLATE


@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    try:
        return jsonify(get_bot_status())
    except Exception as e:
        print(f"Error in /api/status: {e}")
        return jsonify({"error": str(e), "status": "🟠 Error"}), 500


@app.route('/api/orders')
def api_orders():
    """API endpoint for order history"""
    try:
        orders = read_order_history()
        return jsonify({
            "total": len(orders),
            "orders": orders[-20:]  # Last 20 orders
        })
    except Exception as e:
        print(f"Error in /api/orders: {e}")
        return jsonify({"error": str(e), "total": 0, "orders": []}), 500


@app.route('/api/logs')
def api_logs():
    """API endpoint for recent logs"""
    try:
        logs = read_logs()
        return jsonify({
            "logs": logs[-50:]  # Last 50 log entries
        })
    except Exception as e:
        print(f"Error in /api/logs: {e}")
        return jsonify({"error": str(e), "logs": []}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Server error"}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Trading Bot Dashboard")
    print("=" * 60)
    print("Starting dashboard at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=False, port=5000, use_reloader=False, host='127.0.0.1')
