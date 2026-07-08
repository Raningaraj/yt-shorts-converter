#!/bin/bash
# Startup script for Railway with Flask and Streamlit

set -e

echo "[STARTUP] Starting YouTube to Shorts Converter..."

# Set Flask environment
export FLASK_ENV=production
export FLASK_APP=backend/app.py
export FLASK_PORT=5000

# Set Streamlit environment  
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_CLIENT_SHOWERRORDETAILS=false

# Backend URL for Streamlit
export BACKEND_URL=http://localhost:5000

echo "[STARTUP] Starting Flask backend on port 5000..."
python -m flask run --host=0.0.0.0 --port=5000 &
FLASK_PID=$!

echo "[STARTUP] Waiting for Flask to start..."
sleep 3

echo "[STARTUP] Starting Streamlit on port 8501..."
python -m streamlit run streamlit_app.py --logger.level=warning

# If Streamlit exits, kill Flask too
kill $FLASK_PID 2>/dev/null || true
