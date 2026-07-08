#!/usr/bin/env python3
"""
Combined startup script for Railway/Render
Runs Flask backend and Streamlit frontend together
"""
import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Get port from environment
# Railway uses PORT env var for the main service
PORT = os.getenv("PORT", "8501")  # Streamlit runs on exposed port
FLASK_PORT = "5000"  # Flask internal only

# Set Python path
os.environ["PYTHONUNBUFFERED"] = "1"

# Flask config
os.environ["FLASK_ENV"] = "production"
os.environ["FLASK_APP"] = "backend/app.py"

# Streamlit config
os.environ["STREAMLIT_SERVER_PORT"] = PORT
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_CLIENT_SHOWERRORDETAILS"] = "false"
os.environ["STREAMLIT_LOGGER_LEVEL"] = "warning"

# Backend URL for Streamlit to call Flask
os.environ["BACKEND_URL"] = f"http://localhost:{FLASK_PORT}"

print(f"[INIT] Port: {PORT}, Flask: {FLASK_PORT}", flush=True)

processes = []

def cleanup(sig=None, frame=None):
    """Clean shutdown"""
    print("[CLEANUP] Shutting down...", flush=True)
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except:
            try:
                p.kill()
            except:
                pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

# Start Flask backend
print("[STARTUP] Starting Flask...", flush=True)
flask_proc = subprocess.Popen(
    [sys.executable, "-m", "flask", "run", "--host=0.0.0.0", f"--port={FLASK_PORT}"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
processes.append(flask_proc)
time.sleep(2)

# Start Streamlit
print("[STARTUP] Starting Streamlit...", flush=True)
streamlit_proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
processes.append(streamlit_proc)

print("[STARTUP] Both services running", flush=True)

# Keep them alive
try:
    while True:
        if flask_proc.poll() is not None:
            print("[ERROR] Flask died", flush=True)
            break
        if streamlit_proc.poll() is not None:
            print("[ERROR] Streamlit died", flush=True)
            break
        time.sleep(5)
except KeyboardInterrupt:
    cleanup()
