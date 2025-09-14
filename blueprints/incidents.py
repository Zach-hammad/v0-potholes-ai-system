from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.auth import require_auth, get_current_user
from utils.storage import StorageManager
from utils.data_models import Incident
from datetime import datetime
import json

incidents_bp = Blueprint('incidents', __name__)
storage = StorageManager()

@incidents_bp.route('/')
@require_auth()
def index():
    """Incidents list - redirect to dashboard incidents view"""
    return redirect(url_for('dashboard.incidents_list'))

@incidents_bp.route('/create')
@require_auth()
def create():
    """Create new incident form"""
    return render_template('incidents/create.html')

@incidents_bp.route('/create', methods=['POST'])
@require_auth()
def create_post():
    """Handle incident creation"""
    try:
        user = get_current_user()
        
        # Get form data
        location = request.form.get('location', '').strip()
        severity = request.form.get('severity', 'moderate')
        description = request.form.get('description', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        priority = request.form.get('priority', 'medium')
        
        # Validate required fields
        if not location:
            flash('Location is required.', 'error')
            return redirect(url_for('incidents.create'))
        
        # Convert coordinates to float if provided
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
        
        # Create incident
        incident_data = {
            'location': location,
            'severity': severity,
            'description': description,
            'latitude': lat,
            'longitude': lng,
            'priority': priority,
            'status': 'reported',
            'created_by': user['id'],
            'assigned_to': None
        }
        
        # Save incident
        incident_id = storage.save_incident(incident_data)
        
        flash('Incident created successfully!', 'success')
        return redirect(url_for('incidents.view', incident_id=incident_id))
        
    except Exception as e:
        flash('An error occurred while creating the incident. Please try again.', 'error')
        return redirect(url_for('incidents.create'))

@incidents_bp.route('/<incident_id>')
@require_auth()
def view(incident_id):
    """View incident details"""
    incident = storage.get_incident(incident_id)
    
    if not incident:
        flash('Incident not found.', 'error')
        return redirect(url_for('dashboard.incidents_list'))
    
    return render_template('incidents/view.html', incident=incident)

@incidents_bp.route('/<incident_id>/edit')
@require_auth()
def edit(incident_id):
    """Edit incident form"""
    incident = storage.get_incident(incident_id)
    
    if not incident:
        flash('Incident not found.', 'error')
        return redirect(url_for('dashboard.incidents_list'))
    
    return render_template('incidents/edit.html', incident=incident)

@incidents_bp.route('/<incident_id>/edit', methods=['POST'])
@require_auth()
def edit_post(incident_id):
    """Handle incident editing"""
    try:
        incident = storage.get_incident(incident_id)
        
        if not incident:
            flash('Incident not found.', 'error')
            return redirect(url_for('dashboard.incidents_list'))
        
        # Get form data
        location = request.form.get('location', '').strip()
        severity = request.form.get('severity', 'moderate')
        description = request.form.get('description', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'reported')
        assigned_to = request.form.get('assigned_to', '')
        
        # Validate required fields
        if not location:
            flash('Location is required.', 'error')
            return redirect(url_for('incidents.edit', incident_id=incident_id))
        
        # Convert coordinates to float if provided
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
        
        # Update incident
        updates = {
            'location': location,
            'severity': severity,
            'description': description,
            'latitude': lat,
            'longitude': lng,
            'priority': priority,
            'status': status,
            'assigned_to': assigned_to if assigned_to else None
        }
        
        success = storage.update_incident(incident_id, updates)
        
        if success:
            flash('Incident updated successfully!', 'success')
            return redirect(url_for('incidents.view', incident_id=incident_id))
        else:
            flash('Failed to update incident.', 'error')
            return redirect(url_for('incidents.edit', incident_id=incident_id))
        
    except Exception as e:
        flash('An error occurred while updating the incident. Please try again.', 'error')
        return redirect(url_for('incidents.edit', incident_id=incident_id))

@incidents_bp.route('/<incident_id>/delete', methods=['POST'])
@require_auth()
def delete(incident_id):
    """Delete incident"""
    try:
        user = get_current_user()
        
        # Only admins can delete incidents
        if user.get('role') != 'admin':
            flash('You do not have permission to delete incidents.', 'error')
            return redirect(url_for('incidents.view', incident_id=incident_id))
        
        success = storage.delete_incident(incident_id)
        
        if success:
            flash('Incident deleted successfully.', 'success')
        else:
            flash('Failed to delete incident.', 'error')
        
        return redirect(url_for('dashboard.incidents_list'))
        
    except Exception as e:
        flash('An error occurred while deleting the incident.', 'error')
        return redirect(url_for('incidents.view', incident_id=incident_id))

@incidents_bp.route('/<incident_id>/assign', methods=['POST'])
@require_auth()
def assign(incident_id):
    """Assign incident to user"""
    try:
        user_id = request.form.get('user_id')
        current_user = get_current_user()
        
        # If no user_id provided, assign to current user
        if not user_id:
            user_id = current_user['id']
        
        # Update incident
        success = storage.update_incident(incident_id, {
            'assigned_to': user_id,
            'status': 'in-progress'
        })
        
        if success:
            flash('Incident assigned successfully!', 'success')
        else:
            flash('Failed to assign incident.', 'error')
        
        return redirect(url_for('incidents.view', incident_id=incident_id))
        
    except Exception as e:
        flash('An error occurred while assigning the incident.', 'error')
        return redirect(url_for('incidents.view', incident_id=incident_id))

@incidents_bp.route('/<incident_id>/status', methods=['POST'])
@require_auth()
def update_status(incident_id):
    """Update incident status"""
    try:
        status = request.form.get('status')
        
        if not status:
            flash('Status is required.', 'error')
            return redirect(url_for('incidents.view', incident_id=incident_id))
        
        # Update incident
        success = storage.update_incident(incident_id, {'status': status})
        
        if success:
            flash(f'Incident status updated to {status.replace("-", " ").title()}!', 'success')
        else:
            flash('Failed to update incident status.', 'error')
        
        return redirect(url_for('incidents.view', incident_id=incident_id))
        
    except Exception as e:
        flash('An error occurred while updating the incident status.', 'error')
        return redirect(url_for('incidents.view', incident_id=incident_id))

@incidents_bp.route('/<incident_id>/comments', methods=['POST'])
@require_auth()
def add_comment(incident_id):
    """Add comment to incident"""
    try:
        comment_text = request.form.get('comment', '').strip()
        user = get_current_user()
        
        if not comment_text:
            flash('Comment cannot be empty.', 'error')
            return redirect(url_for('incidents.view', incident_id=incident_id))
        
        # Get current incident
        incident = storage.get_incident(incident_id)
        if not incident:
            flash('Incident not found.', 'error')
            return redirect(url_for('dashboard.incidents_list'))
        
        # Add comment to incident
        comments = incident.get('comments', [])
        new_comment = {
            'id': len(comments) + 1,
            'text': comment_text,
            'author': user['username'],
            'author_id': user['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        comments.append(new_comment)
        
        # Update incident with new comment
        success = storage.update_incident(incident_id, {'comments': comments})
        
        if success:
            flash('Comment added successfully!', 'success')
        else:
            flash('Failed to add comment.', 'error')
        
        return redirect(url_for('incidents.view', incident_id=incident_id))
        
    except Exception as e:
        flash('An error occurred while adding the comment.', 'error')
        return redirect(url_for('incidents.view', incident_id=incident_id))

# API Endpoints
@incidents_bp.route('/api/incidents')
@require_auth()
def api_incidents():
    """API endpoint for incidents data"""
    # Get filter parameters
    severity_filter = request.args.get('severity')
    status_filter = request.args.get('status')
    location_filter = request.args.get('location')
    
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
    
    return jsonify(incidents)

@incidents_bp.route('/api/incidents/<incident_id>')
@require_auth()
def api_incident(incident_id):
    """API endpoint for single incident"""
    incident = storage.get_incident(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    return jsonify(incident)

@incidents_bp.route('/api/incidents/<incident_id>/assign', methods=['POST'])
@require_auth()
def api_assign(incident_id):
    """API endpoint to assign incident"""
    data = request.get_json()
    user_id = data.get('user_id')
    current_user = get_current_user()
    
    # If no user_id provided, assign to current user
    if not user_id:
        user_id = current_user['id']
    
    # Update incident
    success = storage.update_incident(incident_id, {
        'assigned_to': user_id,
        'status': 'in-progress'
    })
    
    if success:
        return jsonify({'success': True, 'message': 'Incident assigned successfully'})
    else:
        return jsonify({'error': 'Failed to assign incident'}), 500

@incidents_bp.route('/api/incidents/<incident_id>/status', methods=['POST'])
@require_auth()
def api_update_status(incident_id):
    """API endpoint to update incident status"""
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({'error': 'Status is required'}), 400
    
    # Update incident
    success = storage.update_incident(incident_id, {'status': status})
    
    if success:
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    else:
        return jsonify({'error': 'Failed to update status'}), 500
