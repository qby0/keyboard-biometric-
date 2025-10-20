#!/bin/bash

echo "🚀 Starting Keystroke Biometrics Backend..."

cd "$(dirname "$0")/backend"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo " Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo " Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create data directory
mkdir -p data

echo "✅ Backend is ready!"
echo "🌐 Starting Flask server at http://localhost:5000"
echo ""

# Запуск приложения
python app.py


