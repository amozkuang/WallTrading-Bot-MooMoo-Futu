"""
Simple Web Dashboard for Trading Bot Monitoring
Version 1.0 - 08/29/2026

Monitors bot status, pending trades, and order history
Access at: http://localhost:5000
"""

from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# File paths
ORDER_HISTORY_FILE = "order_history.json"
LOG_FILE = "logs.log"


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
    last_execution = "Never"
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
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    return jsonify(get_bot_status())


@app.route('/api/orders')
def api_orders():
    """API endpoint for order history"""
    orders = read_order_history()
    return jsonify({
        "total": len(orders),
        "orders": orders[-20:]  # Last 20 orders
    })


@app.route('/api/logs')
def api_logs():
    """API endpoint for recent logs"""
    logs = read_logs()
    return jsonify({
        "logs": logs[-50:]  # Last 50 log entries
    })


@app.route('/api/schedule')
def api_schedule():
    """API endpoint for execution schedule"""
    return jsonify({
        "schedule": [
            {
                "day": "Monday",
                "time": "8:00 PM SG",
                "timezone": "UTC+8"
            },
            {
                "day": "Friday",
                "time": "8:00 AM SG",
                "timezone": "UTC+8"
            }
        ],
        "mode": "Paper Trading",
        "bot_capital": "$1,000",
        "max_positions": 4,
        "stocks": ["AAPL", "GOOGL", "JNJ", "ISRG", "TSML", "DIS", "CRWD", "AMD", "MU"]
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Trading Bot Dashboard")
    print("=" * 60)
    print("Starting dashboard at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=True, port=5000, use_reloader=False)
