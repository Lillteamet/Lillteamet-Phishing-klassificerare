#!/bin/bash

# Phishing Classifier Web Application Startup Script

echo "🛡️  Phishing Email Classifier - Web Application"
echo "================================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate venv
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📚 Checking dependencies..."
pip install -q -r requirements.txt

# Check if model exists
if [ ! -f "phishing_model.joblib" ]; then
    echo "❌ Model not found!"
    echo "📋 Training model... (this may take a moment)"
    python train.py
fi

# Check if database exists
if [ -f "phishing_mailbox.db" ]; then
    read -p "📊 Database found. Clear it for a fresh start? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm phishing_mailbox.db
        echo "✓ Database cleared"
    fi
fi

# Start the web app
echo "🚀 Starting web application..."
echo "📱 Open your browser: http://127.0.0.1:5000"
echo "⏸️  Press Ctrl+C to stop"
echo ""

python webapp.py
