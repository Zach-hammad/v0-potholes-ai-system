from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json
import uuid

# Import blueprints
from blueprints.discovery import discovery_bp
from blueprints.dashboard import dashboard_bp
from blueprints.incidents import incidents_bp
from blueprints.admin import admin_bp
from blueprints.chat import chat_bp
from blueprints.about import about_bp
from blueprints.contact import contact_bp

# Import utilities
from utils.auth import require_auth, get_current_user
from utils.storage import StorageManager
from utils.data_models import User, Incident, Report

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize storage manager
storage = StorageManager()

# Register blueprints
app.register_blueprint(discovery_bp, url_prefix='/')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(incidents_bp, url_prefix='/incidents')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(about_bp, url_prefix='/about')
app.register_blueprint(contact_bp, url_prefix='/contact')

# Global template variables
@app.context_processor
def inject_globals():
    return {
        'current_user': get_current_user(),
        'app_name': 'POTHOLES AI',
        'version': '1.0.0'
    }

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
