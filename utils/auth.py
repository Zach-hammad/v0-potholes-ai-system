from functools import wraps
from flask import session, request, jsonify, redirect, url_for, flash
import os
import json
from datetime import datetime

# Mock user data - in production, this would be a database
USERS_FILE = 'data/users.json'

def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        # Create default admin user
        default_users = {
            'admin': {
                'id': 'admin',
                'username': 'admin',
                'email': 'admin@potholes.ai',
                'password_hash': 'pbkdf2:sha256:260000$salt$hash',  # password: admin123
                'role': 'admin',
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True
            }
        }
        save_users(default_users)
        return default_users
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_current_user():
    """Get current logged-in user"""
    if 'user_id' not in session:
        return None
    
    users = load_users()
    return users.get(session['user_id'])

def login_user(username, password):
    """Authenticate and login user"""
    users = load_users()
    
    for user_id, user in users.items():
        if user['username'] == username or user['email'] == username:
            # In production, use proper password hashing
            if password == 'admin123' and user['username'] == 'admin':
                session['user_id'] = user_id
                return user
            # Add proper password verification here
    
    return None

def logout_user():
    """Logout current user"""
    session.pop('user_id', None)

def require_auth(role=None):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('discovery.login'))
            
            if role and user.get('role') != role:
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('discovery.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role):
    """Decorator to require specific role"""
    return require_auth(role=role)
