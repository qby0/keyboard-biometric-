#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API Keystroke Biometrics
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:5000/api"


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_health():
    """Тест проверки здоровья API"""
    print_header("🏥 Проверка здоровья API")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API работает!")
            print(f"📅 Время: {data['timestamp']}")
            return True
        else:
            print(f"❌ API вернул код: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к API")
        print("💡 Убедитесь, что backend запущен: ./start_backend.sh")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def generate_test_keystroke_data(text, base_delay=100, variance=20):
    """Генерация тестовых данных нажатий клавиш"""
    events = []
    timestamp = 1000
    
    for char in text:
        # keydown
        events.append({
            "type": "keydown",
            "key": char,
            "code": f"Key{char.upper()}" if char.isalpha() else "Space",
            "timestamp": timestamp,
            "keyCode": ord(char)
        })
        
        # keyup (через случайное время удержания)
        dwell_time = base_delay + (hash(char) % variance)
        timestamp += dwell_time
        
        events.append({
            "type": "keyup",
            "key": char,
            "code": f"Key{char.upper()}" if char.isalpha() else "Space",
            "timestamp": timestamp,
            "keyCode": ord(char)
        })
        
        # Задержка до следующей клавиши
        flight_time = base_delay + ((hash(char) * 2) % variance)
        timestamp += flight_time
    
    return events


def test_register():
    """Тест регистрации пользователей"""
    print_header("📝 Регистрация тестовых пользователей")
    
    test_users = [
        {"name": "Alice", "delay": 100, "variance": 20},  # Быстрая печать
        {"name": "Bob", "delay": 150, "variance": 30},    # Средняя скорость
        {"name": "Charlie", "delay": 200, "variance": 40}, # Медленная печать
    ]
    
    reference_text = "The quick brown fox jumps over the lazy dog."
    
    for user in test_users:
        print(f"\n👤 Регистрация пользователя: {user['name']}")
        
        # Создаем несколько образцов для каждого пользователя
        for i in range(3):
            keystroke_events = generate_test_keystroke_data(
                reference_text,
                base_delay=user['delay'],
                variance=user['variance']
            )
            
            payload = {
                "username": user['name'],
                "text": reference_text,
                "keystroke_events": keystroke_events
            }
            
            try:
                response = requests.post(
                    f"{API_BASE}/register",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"  ✅ Образец {i+1}/3: {data.get('message')}")
                    else:
                        print(f"  ❌ Ошибка: {data.get('error')}")
                else:
                    print(f"  ❌ HTTP {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
            
            time.sleep(0.5)  # Небольшая задержка


def test_identify():
    """Тест идентификации"""
    print_header("🔍 Тест идентификации")
    
    reference_text = "The quick brown fox jumps over the lazy dog."
    
    # Симулируем Alice
    print("\n🧪 Тест 1: Симуляция стиля Alice (быстрая печать)")
    events = generate_test_keystroke_data(reference_text, base_delay=100, variance=20)
    
    payload = {
        "text": reference_text,
        "keystroke_events": events
    }
    
    try:
        response = requests.post(f"{API_BASE}/identify", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                matches = data.get('matches', [])
                if matches:
                    print(f"\n📊 Топ-{len(matches)} совпадений:")
                    for i, match in enumerate(matches, 1):
                        print(f"  {i}. {match['username']}: "
                              f"{match['similarity']:.1f}% "
                              f"(уверенность: {match['confidence']:.1f}%)")
                else:
                    print("  ℹ️  Совпадений не найдено")
            else:
                print(f"  ❌ Ошибка: {data.get('error')}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Симулируем Charlie
    print("\n🧪 Тест 2: Симуляция стиля Charlie (медленная печать)")
    events = generate_test_keystroke_data(reference_text, base_delay=200, variance=40)
    
    payload = {
        "text": reference_text,
        "keystroke_events": events
    }
    
    try:
        response = requests.post(f"{API_BASE}/identify", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                matches = data.get('matches', [])
                if matches:
                    print(f"\n📊 Топ-{len(matches)} совпадений:")
                    for i, match in enumerate(matches, 1):
                        print(f"  {i}. {match['username']}: "
                              f"{match['similarity']:.1f}% "
                              f"(уверенность: {match['confidence']:.1f}%)")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")


def test_stats():
    """Тест получения статистики"""
    print_header("📊 Статистика системы")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['stats']
                print(f"👥 Всего пользователей: {stats['total_users']}")
                print(f"📝 Всего образцов: {stats['total_samples']}")
                print(f"📈 Среднее образцов на пользователя: {stats['avg_samples_per_user']:.1f}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def test_users():
    """Тест получения списка пользователей"""
    print_header("👥 Список пользователей")
    
    try:
        response = requests.get(f"{API_BASE}/users", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                users = data['users']
                print(f"\nВсего пользователей: {data['total']}\n")
                for user in users:
                    print(f"  • {user['username']}")
                    print(f"    Образцов: {user['samples_count']}")
                    print(f"    Создан: {user['created_at'][:10]}")
                    print()
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def main():
    print("\n" + "="*60)
    print("  🔐 Keystroke Biometrics - Тест API")
    print("="*60)
    
    # Проверка здоровья
    if not test_health():
        return
    
    time.sleep(1)
    
    # Регистрация пользователей
    test_register()
    time.sleep(1)
    
    # Идентификация
    test_identify()
    time.sleep(1)
    
    # Статистика
    test_stats()
    time.sleep(1)
    
    # Список пользователей
    test_users()
    
    print("\n" + "="*60)
    print("  ✅ Все тесты завершены!")
    print("="*60 + "\n")
    
    print("💡 Откройте веб-интерфейс: http://localhost:8000")
    print("   (Запустите: ./start_frontend.sh)\n")


if __name__ == "__main__":
    main()


