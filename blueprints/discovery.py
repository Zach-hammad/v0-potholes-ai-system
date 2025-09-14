from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from utils.auth import login_user, logout_user, get_current_user
from utils.storage import StorageManager
from utils.data_models import Incident
import json

discovery_bp = Blueprint('discovery', __name__)
storage = StorageManager()

@discovery_bp.route('/')
def index():
    """Public homepage with incident map and statistics"""
    # Get recent incidents for public display (anonymized)
    incidents = storage.get_incidents()
    
    # Limit to recent incidents and remove sensitive data
    public_incidents = []
    for incident in incidents[-50:]:  # Last 50 incidents
        public_incident = {
            'id': incident.get('id'),
            'location': incident.get('location', 'Unknown'),
            'severity': incident.get('severity', 'unknown'),
            'status': incident.get('status', 'reported'),
            'latitude': incident.get('latitude'),
            'longitude': incident.get('longitude'),
            'created_at': incident.get('created_at')
        }
        public_incidents.append(public_incident)
    
    # Calculate public statistics
    stats = {
        'total_incidents': len(incidents),
        'resolved_incidents': len([i for i in incidents if i.get('status') == 'resolved']),
        'critical_incidents': len([i for i in incidents if i.get('severity') == 'critical']),
        'in_progress': len([i for i in incidents if i.get('status') == 'in-progress'])
    }
    
    return render_template('discovery/index.html', 
                         incidents=public_incidents, 
                         stats=stats)

@discovery_bp.route('/map')
def map_view():
    """Full-screen map view of all incidents"""
    incidents = storage.get_incidents()
    
    # Filter incidents with location data
    map_incidents = [
        incident for incident in incidents 
        if incident.get('latitude') and incident.get('longitude')
    ]
    
    return render_template('discovery/map.html', incidents=map_incidents)

@discovery_bp.route('/report')
def report_incident():
    """Public incident reporting form"""
    return render_template('discovery/report.html')

@discovery_bp.route('/report', methods=['POST'])
def submit_report():
    """Handle incident report submission"""
    try:
        # Get form data
        location = request.form.get('location', '').strip()
        severity = request.form.get('severity', 'moderate')
        description = request.form.get('description', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Validate required fields
        if not location:
            flash('Location is required.', 'error')
            return redirect(url_for('discovery.report_incident'))
        
        # Convert coordinates to float if provided
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
        
        # Create incident
        incident = Incident(
            location=location,
            severity=severity,
            description=description,
            latitude=lat,
            longitude=lng
        )
        
        # Save incident
        incident_id = storage.save_incident(incident.to_dict())
        
        flash('Thank you! Your incident report has been submitted successfully.', 'success')
        return redirect(url_for('discovery.report_success', incident_id=incident_id))
        
    except Exception as e:
        flash('An error occurred while submitting your report. Please try again.', 'error')
        return redirect(url_for('discovery.report_incident'))

@discovery_bp.route('/report/success/<incident_id>')
def report_success(incident_id):
    """Report submission success page"""
    incident = storage.get_incident(incident_id)
    return render_template('discovery/report_success.html', incident=incident)

@discovery_bp.route('/login')
def login():
    """Login page for operators and admins"""
    if get_current_user():
        return redirect(url_for('dashboard.index'))
    return render_template('discovery/login.html')

@discovery_bp.route('/login', methods=['POST'])
def login_post():
    """Handle login form submission"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        flash('Please enter both username and password.', 'error')
        return redirect(url_for('discovery.login'))
    
    user = login_user(username, password)
    if user:
        flash(f'Welcome back, {user["username"]}!', 'success')
        return redirect(url_for('dashboard.index'))
    else:
        flash('Invalid username or password.', 'error')
        return redirect(url_for('discovery.login'))

@discovery_bp.route('/logout')
def logout():
    """Logout current user"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('discovery.index'))

@discovery_bp.route('/api/incidents')
def api_incidents():
    """API endpoint for incident data (public, anonymized)"""
    incidents = storage.get_incidents()
    
    # Return anonymized incident data
    public_incidents = []
    for incident in incidents:
        public_incident = {
            'id': incident.get('id'),
            'location': incident.get('location'),
            'severity': incident.get('severity'),
            'status': incident.get('status'),
            'latitude': incident.get('latitude'),
            'longitude': incident.get('longitude'),
            'created_at': incident.get('created_at')
        }
        public_incidents.append(public_incident)
    
    return jsonify(public_incidents)

@discovery_bp.route('/api/stats')
def api_stats():
    """API endpoint for public statistics"""
    incidents = storage.get_incidents()
    
    stats = {
        'total': len(incidents),
        'severity': {
            'critical': len([i for i in incidents if i.get('severity') == 'critical']),
            'major': len([i for i in incidents if i.get('severity') == 'major']),
            'moderate': len([i for i in incidents if i.get('severity') == 'moderate']),
            'minor': len([i for i in incidents if i.get('severity') == 'minor'])
        },
        'status': {
            'reported': len([i for i in incidents if i.get('status') == 'reported']),
            'in-progress': len([i for i in incidents if i.get('status') == 'in-progress']),
            'resolved': len([i for i in incidents if i.get('status') == 'resolved'])
        }
    }
    
    return jsonify(stats)
