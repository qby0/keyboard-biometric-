from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import yaml
import os
from datetime import datetime
from ml_model import KeystrokeBiometrics
from data_processor import DataProcessor

app = Flask(__name__)
CORS(app)

# Initialization
data_processor = DataProcessor()
biometric_model = KeystrokeBiometrics()

# Data path
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, 'users.yaml')
KEYSTROKE_DATA_FILE = os.path.join(DATA_DIR, 'keystroke_data.yaml')

# Legacy JSON files for migration
USERS_JSON_FILE = os.path.join(DATA_DIR, 'users.json')
KEYSTROKE_JSON_FILE = os.path.join(DATA_DIR, 'keystroke_data.json')


def load_data():
    """Load user data and keystrokes (with auto-migration from JSON)"""
    users = {}
    keystroke_data = []
    
    # Migrate from JSON to YAML if needed
    if os.path.exists(USERS_JSON_FILE) and not os.path.exists(USERS_FILE):
        print("Migrating data from JSON to YAML...")
        with open(USERS_JSON_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        with open(KEYSTROKE_JSON_FILE, 'r', encoding='utf-8') as f:
            keystroke_data = json.load(f)
        save_data(users, keystroke_data)
        print("Migration complete!")
    
    # Load from YAML
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = yaml.safe_load(f) or {}
    
    if os.path.exists(KEYSTROKE_DATA_FILE):
        with open(KEYSTROKE_DATA_FILE, 'r', encoding='utf-8') as f:
            keystroke_data = yaml.safe_load(f) or []
    
    return users, keystroke_data


def save_data(users, keystroke_data):
    """Save data to YAML (with JSON backup)"""
    # Save to YAML (primary format)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(users, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    with open(KEYSTROKE_DATA_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(keystroke_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # JSON backup for compatibility
    with open(USERS_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    
    with open(KEYSTROKE_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(keystroke_data, f, indent=2, ensure_ascii=False)


@app.route('/api/register', methods=['POST'])
def register_user():
    """Register new user with keystroke pattern"""
    try:
        data = request.json
        username = data.get('username')
        keystroke_events = data.get('keystroke_events', [])
        text = data.get('text', '')
        
        if not username or not keystroke_events:
            return jsonify({'error': 'Missing username or keystroke data'}), 400
        
        users, keystroke_data = load_data()
        
        # Process keystroke data
        features = data_processor.extract_features(keystroke_events, text)
        
        # Create or update user
        if username not in users:
            users[username] = {
                'created_at': datetime.now().isoformat(),
                'samples_count': 0,
                'features': []
            }
        
        users[username]['samples_count'] += 1
        users[username]['features'].append(features)
        users[username]['last_updated'] = datetime.now().isoformat()
        
        # Save raw data
        keystroke_data.append({
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'text': text,
            'events': keystroke_events,
            'features': features
        })
        
        save_data(users, keystroke_data)
        
        # Retrain model
        biometric_model.train(users)
        
        return jsonify({
            'success': True,
            'message': f'User {username} registered/updated successfully',
            'samples_count': users[username]['samples_count']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/identify', methods=['POST'])
def identify_user():
    """Identify user by keystroke pattern"""
    try:
        data = request.json
        keystroke_events = data.get('keystroke_events', [])
        text = data.get('text', '')
        
        if not keystroke_events:
            return jsonify({'error': 'Missing keystroke data'}), 400
        
        users, _ = load_data()
        
        if not users:
            return jsonify({
                'success': True,
                'matches': [],
                'message': 'No users in database yet'
            })
        
        # Extract features
        features = data_processor.extract_features(keystroke_events, text)
        
        # Get similar users
        matches = biometric_model.identify(features, users)
        
        return jsonify({
            'success': True,
            'matches': matches[:5]  # Top-5 similar users
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get list of all users"""
    try:
        users, _ = load_data()
        
        user_list = []
        for username, data in users.items():
            user_list.append({
                'username': username,
                'samples_count': data['samples_count'],
                'created_at': data.get('created_at', 'N/A'),
                'last_updated': data.get('last_updated', 'N/A')
            })
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total': len(user_list)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<username>', methods=['GET'])
def get_user_details(username):
    """Get detailed user information with averaged parameters"""
    try:
        import numpy as np
        users, _ = load_data()
        
        if username not in users:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = users[username]
        features_list = user_data.get('features', [])
        
        if not features_list:
            return jsonify({'error': 'No samples found for user'}), 404
        
        # Average all parameters
        averaged_features = {}
        feature_keys = features_list[0].keys()
        
        for key in feature_keys:
            if key in ['raw_dwell_times', 'raw_latencies']:
                # For raw data, take last sample
                averaged_features[key] = features_list[-1].get(key, [])
            else:
                # Average numeric values
                values = [f.get(key, 0) for f in features_list]
                averaged_features[key] = float(np.mean(values))
        
        # Variation statistics for each parameter
        variation_stats = {}
        for key in feature_keys:
            if key not in ['raw_dwell_times', 'raw_latencies']:
                values = [f.get(key, 0) for f in features_list]
                if len(values) > 1:
                    variation_stats[key] = {
                        'min': float(np.min(values)),
                        'max': float(np.max(values)),
                        'std': float(np.std(values)),
                        'mean': float(np.mean(values))
                    }
        
        return jsonify({
            'success': True,
            'user': {
                'username': username,
                'samples_count': user_data['samples_count'],
                'created_at': user_data.get('created_at', 'N/A'),
                'last_updated': user_data.get('last_updated', 'N/A'),
                'averaged_features': averaged_features,
                'variation_stats': variation_stats,
                'all_samples': features_list
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        users, keystroke_data = load_data()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': len(users),
                'total_samples': len(keystroke_data),
                'avg_samples_per_user': len(keystroke_data) / len(users) if users else 0
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

