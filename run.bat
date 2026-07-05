@echo off
REM ===================================================================
REM YouTube to Shorts Converter - Windows Runner
REM This script activates the virtual environment and runs the backend
REM ===================================================================

echo.
echo ===============================================
echo  YT Shorts Converter - Starting...
echo ===============================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Change to backend directory
cd backend

REM Run the Flask app
echo.
echo Starting Flask server...
echo Open your browser to: http://localhost:5000
echo.
python app.py

pause
