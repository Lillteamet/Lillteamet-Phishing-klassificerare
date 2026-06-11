@echo off
REM Phishing Classifier Web Application Startup Script for Windows

echo.
echo 🛡️  Phishing Email Classifier - Web Application
echo ================================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo 📚 Checking dependencies...
pip install -q -r requirements.txt

REM Check if model exists
if not exist "phishing_model.joblib" (
    echo ❌ Model not found!
    echo 📋 Training model... (this may take a moment)
    python train.py
)

REM Start the web app
echo.
echo 🚀 Starting web application...
echo 📱 Open your browser: http://127.0.0.1:5000
echo ⏸️  Press Ctrl+C to stop
echo.

python webapp.py
pause
