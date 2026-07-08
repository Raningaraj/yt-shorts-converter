#!/usr/bin/env python
"""
Startup script for Railway/Render that manages both Flask and Streamlit processes
"""
import os
import sys
import subprocess
import time
import signal

# Get port from environment or use defaults
FLASK_PORT = os.getenv("FLASK_PORT", "5000")
STREAMLIT_PORT = os.getenv("PORT", "8501")  # Railway/Render use PORT for Streamlit

# Set environment variables for Flask
os.environ["FLASK_ENV"] = "production"
os.environ["FLASK_APP"] = "backend/app.py"

# Set environment variables for Streamlit
os.environ["STREAMLIT_SERVER_PORT"] = STREAMLIT_PORT
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_CLIENT_SHOWERRORDETAILS"] = "false"

# Backend URL for Streamlit to communicate with Flask
os.environ["BACKEND_URL"] = f"http://localhost:{FLASK_PORT}"

processes = []

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\n[STARTUP] Shutting down services...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_flask():
    """Start Flask backend"""
    print(f"[STARTUP] Starting Flask backend on port {FLASK_PORT}...")
    cmd = [
        sys.executable, 
        "-m", 
        "flask", 
        "run", 
        "--host=0.0.0.0",
        f"--port={FLASK_PORT}"
    ]
    process = subprocess.Popen(cmd, cwd=".")
    processes.append(process)
    return process

def start_streamlit():
    """Start Streamlit frontend"""
    print(f"[STARTUP] Starting Streamlit app on port {STREAMLIT_PORT}...")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--logger.level=warning"
    ]
    process = subprocess.Popen(cmd, cwd=".")
    processes.append(process)
    return process

if __name__ == "__main__":
    print("[STARTUP] Initializing YouTube to Shorts Converter...")
    
    # Start both services
    flask_process = start_flask()
    time.sleep(3)  # Give Flask time to start
    
    streamlit_process = start_streamlit()
    
    print(f"[STARTUP] Both services started!")
    print(f"  - Flask backend: http://localhost:{FLASK_PORT}")
    print(f"  - Streamlit frontend: http://localhost:{STREAMLIT_PORT}")
    
    # Keep processes running
    try:
        while True:
            # Check if either process has died
            if not flask_process.poll() is None:
                print("[ERROR] Flask backend crashed!")
                sys.exit(1)
            if not streamlit_process.poll() is None:
                print("[ERROR] Streamlit app crashed!")
                sys.exit(1)
            
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(None, None)
