#!/usr/bin/env python3
"""
Test script for Keystroke Biometrics API
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
    """API health check test"""
    print_header("🏥 API Health Check")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is up!")
            print(f"📅 Time: {data['timestamp']}")
            return True
        else:
            print(f"❌ API returned code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to API")
        print("💡 Make sure backend is running: ./start_backend.sh")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_test_keystroke_data(text, base_delay=100, variance=20):
    """Generate synthetic keystroke events"""
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
        
        # keyup (after randomized dwell time)
        dwell_time = base_delay + (hash(char) % variance)
        timestamp += dwell_time
        
        events.append({
            "type": "keyup",
            "key": char,
            "code": f"Key{char.upper()}" if char.isalpha() else "Space",
            "timestamp": timestamp,
            "keyCode": ord(char)
        })
        
        # delay before next key
        flight_time = base_delay + ((hash(char) * 2) % variance)
        timestamp += flight_time
    
    return events


def test_register():
    """User registration test"""
    print_header("📝 Register test users")
    
    test_users = [
        {"name": "Alice", "delay": 100, "variance": 20},  # fast typing
        {"name": "Bob", "delay": 150, "variance": 30},    # medium speed
        {"name": "Charlie", "delay": 200, "variance": 40}, # slow typing
    ]
    
    reference_text = "The quick brown fox jumps over the lazy dog."
    
    for user in test_users:
        print(f"\n👤 Registering user: {user['name']}")
        
        # Create multiple samples per user
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
                        print(f"  ✅ Sample {i+1}/3: {data.get('message')}")
                    else:
                        print(f"  ❌ Error: {data.get('error')}")
                else:
                    print(f"  ❌ HTTP {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            time.sleep(0.5)  # small delay


def test_identify():
    """Identification test"""
    print_header("🔍 Identification test")
    
    reference_text = "The quick brown fox jumps over the lazy dog."
    
    # Simulate Alice
    print("\n🧪 Test 1: Simulate Alice (fast typing)")
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
                    print(f"\n📊 Top-{len(matches)} matches:")
                    for i, match in enumerate(matches, 1):
                        print(f"  {i}. {match['username']}: "
                              f"{match['similarity']:.1f}% "
                              f"(confidence: {match['confidence']:.1f}%)")
                else:
                    print("  ℹ️  No matches found")
            else:
                print(f"  ❌ Error: {data.get('error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Simulate Charlie
    print("\n🧪 Test 2: Simulate Charlie (slow typing)")
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
                    print(f"\n📊 Top-{len(matches)} matches:")
                    for i, match in enumerate(matches, 1):
                        print(f"  {i}. {match['username']}: "
                              f"{match['similarity']:.1f}% "
                              f"(confidence: {match['confidence']:.1f}%)")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_stats():
    """System stats test"""
    print_header("📊 System statistics")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['stats']
                print(f"👥 Total users: {stats['total_users']}")
                print(f"📝 Total samples: {stats['total_samples']}")
                print(f"📈 Avg samples per user: {stats['avg_samples_per_user']:.1f}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_users():
    """Users list test"""
    print_header("👥 Registered Users")
    
    try:
        response = requests.get(f"{API_BASE}/users", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                users = data['users']
                print(f"\nTotal users: {data['total']}\n")
                for user in users:
                    print(f"  • {user['username']}")
                    print(f"    Samples: {user['samples_count']}")
                    print(f"    Created: {user['created_at'][:10]}")
                    print()
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n" + "="*60)
    print("  🔐 Keystroke Biometrics - API Test")
    print("="*60)
    
    # Health check
    if not test_health():
        return
    
    time.sleep(1)
    
    # Registration
    test_register()
    time.sleep(1)
    
    # Identification
    test_identify()
    time.sleep(1)
    
    # Statistics
    test_stats()
    time.sleep(1)
    
    # Users list
    test_users()
    
    print("\n" + "="*60)
    print("  ✅ All tests completed!")
    print("="*60 + "\n")
    
    print("💡 Open web UI: http://localhost:8000")
    print("   (Run: ./start_frontend.sh)\n")


if __name__ == "__main__":
    main()


