@echo off
REM ===================================================================
REM YouTube to Shorts Converter - Windows Setup
REM This script sets up the virtual environment and installs dependencies
REM ===================================================================

echo.
echo ===============================================
echo  YT Shorts Converter - Setup
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

echo.
echo [2/4] Creating virtual environment...
if exist "venv\" (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
)

echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  Setup Complete!
echo ===============================================
echo.
echo Next steps:
echo 1. Create .env file in backend/ folder with:
echo    GROQ_API_KEY=your_groq_api_key_here
echo    (Get free key at https://console.groq.com)
echo.
echo 2. Run the application with:
echo    python run.py
echo    OR
echo    run.bat
echo.
echo 3. Open browser to: http://localhost:5000
echo.

pause
