#!/bin/bash

echo "🚀 Запуск Keystroke Biometrics Frontend..."

cd "$(dirname "$0")/frontend"

echo "✅ Frontend готов!"
echo "🌐 Открытие браузера на http://localhost:8000"
echo ""
echo "💡 Убедитесь, что backend запущен (start_backend.sh)"
echo ""

# Запуск простого HTTP сервера
python3 -m http.server 8000


