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

# Check if port 5000 is already in use
if lsof -i :5000 >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":5000 " || ss -tuln 2>/dev/null | grep -q ":5000 "; then
    echo "⚠️  Port 5000 is already in use!"
    echo ""
    echo "Options:"
    echo "  1. Stop the existing process and continue"
    echo "  2. Exit"
    echo ""
    read -p "Your choice (1-2): " choice
    
    case $choice in
        1)
            echo "Stopping process on port 5000..."
            lsof -ti :5000 | xargs kill -9 2>/dev/null || \
            (netstat -tuln 2>/dev/null | grep ":5000 " | awk '{print $7}' | cut -d'/' -f1 | xargs kill -9 2>/dev/null) || \
            (ss -tuln 2>/dev/null | grep ":5000 " | awk '{print $6}' | cut -d':' -f2 | xargs kill -9 2>/dev/null)
            sleep 1
            ;;
        2)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
fi

echo "✅ Backend is ready!"
echo "🌐 Starting Flask server at http://localhost:5000"
echo ""

# Запуск приложения
python app.py


