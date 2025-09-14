from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.auth import require_auth, get_current_user
from utils.storage import StorageManager
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)
storage = StorageManager()

@dashboard_bp.route('/')
@require_auth()
def index():
    """Main dashboard overview"""
    user = get_current_user()
    
    # Get incidents data
    incidents = storage.get_incidents()
    
    # Calculate statistics
    stats = calculate_dashboard_stats(incidents)
    
    # Get recent incidents
    recent_incidents = sorted(incidents, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    
    # Get assigned incidents for current user
    assigned_incidents = [
        incident for incident in incidents 
        if incident.get('assigned_to') == user['id']
    ]
    
    return render_template('dashboard/index.html', 
                         stats=stats,
                         recent_incidents=recent_incidents,
                         assigned_incidents=assigned_incidents,
                         user=user)

@dashboard_bp.route('/incidents')
@require_auth()
def incidents_list():
    """Incidents list view with filters"""
    # Get filter parameters
    severity_filter = request.args.get('severity')
    status_filter = request.args.get('status')
    location_filter = request.args.get('location')
    assigned_filter = request.args.get('assigned')
    
    # Build filters dict
    filters = {}
    if severity_filter:
        filters['severity'] = severity_filter
    if status_filter:
        filters['status'] = status_filter
    if location_filter:
        filters['location'] = location_filter
    
    # Get filtered incidents
    incidents = storage.get_incidents(filters)
    
    # Filter by assignment if specified
    if assigned_filter == 'me':
        user = get_current_user()
        incidents = [i for i in incidents if i.get('assigned_to') == user['id']]
    elif assigned_filter == 'unassigned':
        incidents = [i for i in incidents if not i.get('assigned_to')]
    
    # Sort by priority and date
    incidents = sorted(incidents, key=lambda x: (
        {'critical': 0, 'major': 1, 'moderate': 2, 'minor': 3}.get(x.get('severity', 'minor'), 3),
        x.get('created_at', '')
    ), reverse=True)
    
    return render_template('dashboard/incidents.html', 
                         incidents=incidents,
                         filters={
                             'severity': severity_filter,
                             'status': status_filter,
                             'location': location_filter,
                             'assigned': assigned_filter
                         })

@dashboard_bp.route('/analytics')
@require_auth()
def analytics():
    """Analytics and reporting dashboard"""
    incidents = storage.get_incidents()
    
    # Generate analytics data
    analytics_data = generate_analytics_data(incidents)
    
    return render_template('dashboard/analytics.html', 
                         analytics=analytics_data)

@dashboard_bp.route('/profile')
@require_auth()
def profile():
    """User profile and settings"""
    user = get_current_user()
    
    # Get user's activity stats
    incidents = storage.get_incidents()
    user_stats = {
        'assigned_incidents': len([i for i in incidents if i.get('assigned_to') == user['id']]),
        'resolved_incidents': len([i for i in incidents if i.get('assigned_to') == user['id'] and i.get('status') == 'resolved']),
        'pending_incidents': len([i for i in incidents if i.get('assigned_to') == user['id'] and i.get('status') != 'resolved'])
    }
    
    return render_template('dashboard/profile.html', 
                         user=user,
                         user_stats=user_stats)

# API Endpoints
@dashboard_bp.route('/api/stats')
@require_auth()
def api_stats():
    """API endpoint for dashboard statistics"""
    incidents = storage.get_incidents()
    stats = calculate_dashboard_stats(incidents)
    return jsonify(stats)

@dashboard_bp.route('/api/timeline')
@require_auth()
def api_timeline():
    """API endpoint for timeline data"""
    incidents = storage.get_incidents()
    
    # Generate timeline data for last 30 days
    timeline_data = generate_timeline_data(incidents, days=30)
    
    return jsonify(timeline_data)

@dashboard_bp.route('/api/assign', methods=['POST'])
@require_auth()
def api_assign_incident():
    """API endpoint to assign incident to user"""
    data = request.get_json()
    incident_id = data.get('incident_id')
    user_id = data.get('user_id')
    
    if not incident_id:
        return jsonify({'error': 'Incident ID required'}), 400
    
    # If no user_id provided, assign to current user
    if not user_id:
        user_id = get_current_user()['id']
    
    # Update incident
    success = storage.update_incident(incident_id, {
        'assigned_to': user_id,
        'status': 'in-progress'
    })
    
    if success:
        return jsonify({'success': True, 'message': 'Incident assigned successfully'})
    else:
        return jsonify({'error': 'Failed to assign incident'}), 500

@dashboard_bp.route('/api/update-status', methods=['POST'])
@require_auth()
def api_update_status():
    """API endpoint to update incident status"""
    data = request.get_json()
    incident_id = data.get('incident_id')
    status = data.get('status')
    
    if not incident_id or not status:
        return jsonify({'error': 'Incident ID and status required'}), 400
    
    # Update incident
    success = storage.update_incident(incident_id, {'status': status})
    
    if success:
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    else:
        return jsonify({'error': 'Failed to update status'}), 500

# Helper functions
def calculate_dashboard_stats(incidents):
    """Calculate dashboard statistics"""
    total = len(incidents)
    
    # Status counts
    status_counts = {
        'reported': len([i for i in incidents if i.get('status') == 'reported']),
        'in-progress': len([i for i in incidents if i.get('status') == 'in-progress']),
        'resolved': len([i for i in incidents if i.get('status') == 'resolved'])
    }
    
    # Severity counts
    severity_counts = {
        'critical': len([i for i in incidents if i.get('severity') == 'critical']),
        'major': len([i for i in incidents if i.get('severity') == 'major']),
        'moderate': len([i for i in incidents if i.get('severity') == 'moderate']),
        'minor': len([i for i in incidents if i.get('severity') == 'minor'])
    }
    
    # Calculate resolution rate
    resolution_rate = (status_counts['resolved'] / total * 100) if total > 0 else 0
    
    # Recent activity (last 7 days)
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    recent_incidents = [
        i for i in incidents 
        if i.get('created_at', '') > week_ago
    ]
    
    return {
        'total': total,
        'status': status_counts,
        'severity': severity_counts,
        'resolution_rate': round(resolution_rate, 1),
        'recent_count': len(recent_incidents),
        'unassigned': len([i for i in incidents if not i.get('assigned_to')])
    }

def generate_analytics_data(incidents):
    """Generate analytics data for charts"""
    # Monthly trend data
    monthly_data = {}
    for incident in incidents:
        created_at = incident.get('created_at', '')
        if created_at:
            try:
                date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                month_key = date.strftime('%Y-%m')
                monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
            except:
                continue
    
    # Sort months
    sorted_months = sorted(monthly_data.keys())
    
    return {
        'monthly_trend': {
            'labels': [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in sorted_months],
            'data': [monthly_data[m] for m in sorted_months]
        },
        'severity_distribution': {
            'critical': len([i for i in incidents if i.get('severity') == 'critical']),
            'major': len([i for i in incidents if i.get('severity') == 'major']),
            'moderate': len([i for i in incidents if i.get('severity') == 'moderate']),
            'minor': len([i for i in incidents if i.get('severity') == 'minor'])
        },
        'status_distribution': {
            'reported': len([i for i in incidents if i.get('status') == 'reported']),
            'in-progress': len([i for i in incidents if i.get('status') == 'in-progress']),
            'resolved': len([i for i in incidents if i.get('status') == 'resolved'])
        }
    }

def generate_timeline_data(incidents, days=30):
    """Generate timeline data for the last N days"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Create daily buckets
    daily_counts = {}
    current_date = start_date
    while current_date <= end_date:
        date_key = current_date.strftime('%Y-%m-%d')
        daily_counts[date_key] = 0
        current_date += timedelta(days=1)
    
    # Count incidents per day
    for incident in incidents:
        created_at = incident.get('created_at', '')
        if created_at:
            try:
                date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if start_date <= date <= end_date:
                    date_key = date.strftime('%Y-%m-%d')
                    daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            except:
                continue
    
    # Sort dates
    sorted_dates = sorted(daily_counts.keys())
    
    return {
        'labels': [datetime.strptime(d, '%Y-%m-%d').strftime('%m/%d') for d in sorted_dates],
        'data': [daily_counts[d] for d in sorted_dates]
    }
