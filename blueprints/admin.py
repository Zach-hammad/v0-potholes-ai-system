from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from functools import wraps
from utils.auth import require_auth, get_current_user
from utils.data_models import get_all_users, get_user_by_id, update_user, delete_user, get_system_stats, get_audit_logs
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('discovery.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@require_auth
@admin_required
def index():
    """Admin dashboard overview"""
    stats = get_system_stats()
    recent_logs = get_audit_logs(limit=10)
    return render_template('admin/index.html', stats=stats, recent_logs=recent_logs)

@admin_bp.route('/users')
@require_auth
@admin_required
def users():
    """User management interface"""
    users = get_all_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@require_auth
@admin_required
def user_detail(user_id):
    """View/edit specific user"""
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_detail.html', user=user)

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@require_auth
@admin_required
def edit_user(user_id):
    """Update user details"""
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    
    # Update user data
    update_data = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'role': request.form.get('role'),
        'active': request.form.get('active') == 'on'
    }
    
    if update_user(user_id, update_data):
        flash('User updated successfully.', 'success')
    else:
        flash('Failed to update user.', 'error')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@require_auth
@admin_required
def delete_user_route(user_id):
    """Delete user account"""
    if delete_user(user_id):
        flash('User deleted successfully.', 'success')
    else:
        flash('Failed to delete user.', 'error')
    return redirect(url_for('admin.users'))

@admin_bp.route('/system')
@require_auth
@admin_required
def system():
    """System configuration and settings"""
    config = {
        'tigris_configured': bool(os.getenv('TIGRIS_ENDPOINT')),
        'ai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'maps_configured': bool(os.getenv('MAPBOX_ACCESS_TOKEN')),
        'email_configured': bool(os.getenv('SMTP_SERVER')),
        'debug_mode': os.getenv('FLASK_ENV') == 'development'
    }
    return render_template('admin/system.html', config=config)

@admin_bp.route('/logs')
@require_auth
@admin_required
def logs():
    """System audit logs"""
    page = request.args.get('page', 1, type=int)
    logs = get_audit_logs(page=page, per_page=50)
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/api/stats')
@require_auth
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = get_system_stats()
    return jsonify(stats)
