# dashboard.py
#
# This script creates a Flask web server with Socket.IO to provide a real-time
# monitoring dashboard for the AutoGen autonomous agent system. It listens for
# events from the main script and broadcasts them to connected web clients.

from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Thread
import logging
import os

# Suppress verbose logging from server libraries to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
WEBSOCKET_PORT=os.getenv('WEBSOCKET_PORT', '5005')
app = Flask(__name__)
# Use a simple secret key for Socket.IO
app.config['SECRET_KEY'] = 'secret!'
# Use the simple-websocket server which is great for development
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

@app.route('/')
def index():
    """Serves the main dashboard HTML page."""
    return render_template('index.html')

def run_dashboard():
    """
    Runs the Flask-SocketIO server in a background thread.
    Running on port 5005 to avoid conflicts with other common dev ports.
    """
    # Use allow_unsafe_werkzeug=True for development environments
    socketio.run(app, port=WEBSOCKET_PORT, debug=False, allow_unsafe_werkzeug=True)

def start_dashboard_server_in_thread():
    """Starts the dashboard server in a daemon thread."""
    print("📊 Starting monitoring dashboard in a background thread...")
    # The daemon=True flag ensures the thread will exit when the main script exits
    dashboard_thread = Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    print(" Dashboard is running at http://127.0.0.1:{}/".format(WEBSOCKET_PORT))
    return socketio

# Explicit exports
__all__ = [
    "app",
    "socketio",
    "run_dashboard",
    "start_dashboard_server_in_thread",
]

if __name__ == '__main__':
    print("This script is not meant to be run directly. It is imported by main.py.")
    print("Starting dashboard for direct testing...")
    socketio.run(app, port=5005, debug=True)
