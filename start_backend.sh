#!/bin/bash

echo "🚀 Запуск Keystroke Biometrics Backend..."

cd "$(dirname "$0")/backend"

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install -q -r requirements.txt

# Создание директории для данных
mkdir -p data

echo "✅ Backend готов!"
echo "🌐 Запуск Flask сервера на http://localhost:5000"
echo ""

# Запуск приложения
python app.py


