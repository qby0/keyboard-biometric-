#!/bin/bash

echo "🚀 Starting Keystroke Biometrics Frontend..."

cd "$(dirname "$0")/frontend"

echo "✅ Frontend is ready!"
echo "🌐 Open http://localhost:8000 in your browser"
echo ""
echo "💡 Make sure the backend is running (start_backend.sh)"
echo ""

# Start simple HTTP server
python3 -m http.server 8000


