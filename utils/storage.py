import os
import json
from datetime import datetime
import uuid

class StorageManager:
    """Handles data storage operations"""
    
    def __init__(self):
        self.data_dir = 'data'
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create subdirectories
        subdirs = ['incidents', 'reports', 'uploads', 'exports']
        for subdir in subdirs:
            os.makedirs(os.path.join(self.data_dir, subdir), exist_ok=True)
    
    def save_json(self, filename, data):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_json(self, filename, default=None):
        """Load data from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            return default or {}
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default or {}
    
    def save_incident(self, incident_data):
        """Save incident data"""
        incidents = self.load_json('incidents.json', {})
        incident_id = str(uuid.uuid4())
        incident_data['id'] = incident_id
        incident_data['created_at'] = datetime.utcnow().isoformat()
        incidents[incident_id] = incident_data
        self.save_json('incidents.json', incidents)
        return incident_id
    
    def get_incidents(self, filters=None):
        """Get incidents with optional filters"""
        incidents = self.load_json('incidents.json', {})
        
        if not filters:
            return list(incidents.values())
        
        filtered = []
        for incident in incidents.values():
            match = True
            
            if filters.get('severity') and incident.get('severity') != filters['severity']:
                match = False
            if filters.get('status') and incident.get('status') != filters['status']:
                match = False
            if filters.get('location') and filters['location'].lower() not in incident.get('location', '').lower():
                match = False
            
            if match:
                filtered.append(incident)
        
        return filtered
    
    def get_incident(self, incident_id):
        """Get single incident by ID"""
        incidents = self.load_json('incidents.json', {})
        return incidents.get(incident_id)
    
    def update_incident(self, incident_id, updates):
        """Update incident data"""
        incidents = self.load_json('incidents.json', {})
        if incident_id in incidents:
            incidents[incident_id].update(updates)
            incidents[incident_id]['updated_at'] = datetime.utcnow().isoformat()
            self.save_json('incidents.json', incidents)
            return True
        return False
    
    def delete_incident(self, incident_id):
        """Delete incident"""
        incidents = self.load_json('incidents.json', {})
        if incident_id in incidents:
            del incidents[incident_id]
            self.save_json('incidents.json', incidents)
            return True
        return False
