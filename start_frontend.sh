#!/bin/bash

echo "🚀 Starting Keystroke Biometrics Frontend..."

cd "$(dirname "$0")/frontend"

# Check if port 8000 is already in use
if lsof -i :8000 >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":8000 " || ss -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "⚠️  Port 8000 is already in use!"
    echo ""
    echo "Options:"
    echo "  1. Stop the existing process and continue"
    echo "  2. Use a different port (8001)"
    echo "  3. Exit"
    echo ""
    read -p "Your choice (1-3): " choice
    
    case $choice in
        1)
            echo "Stopping process on port 8000..."
            lsof -ti :8000 | xargs kill -9 2>/dev/null || \
            (netstat -tuln 2>/dev/null | grep ":8000 " | awk '{print $7}' | cut -d'/' -f1 | xargs kill -9 2>/dev/null) || \
            (ss -tuln 2>/dev/null | grep ":8000 " | awk '{print $6}' | cut -d':' -f2 | xargs kill -9 2>/dev/null)
            sleep 1
            ;;
        2)
            PORT=8001
            echo "Using port $PORT instead..."
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
else
    PORT=8000
fi

echo "✅ Frontend is ready!"
echo "🌐 Open http://localhost:${PORT} in your browser"
echo ""
echo "💡 Make sure the backend is running (start_backend.sh)"
echo ""

# Start simple HTTP server
python3 -m http.server ${PORT}


