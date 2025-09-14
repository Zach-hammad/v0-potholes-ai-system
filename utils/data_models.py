from datetime import datetime
from typing import Dict, List, Optional

class User:
    """User data model"""
    
    def __init__(self, user_id: str, username: str, email: str, role: str = 'operator'):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.created_at = datetime.utcnow()
        self.is_active = True
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

class Incident:
    """Incident data model"""
    
    def __init__(self, location: str, severity: str, description: str = '', 
                 latitude: float = None, longitude: float = None):
        self.id = None  # Set by storage manager
        self.location = location
        self.severity = severity
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.status = 'reported'
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.assigned_to = None
        self.priority = self._calculate_priority()
    
    def _calculate_priority(self) -> str:
        """Calculate priority based on severity"""
        severity_priority = {
            'critical': 'high',
            'major': 'high',
            'moderate': 'medium',
            'minor': 'low'
        }
        return severity_priority.get(self.severity, 'medium')
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'location': self.location,
            'severity': self.severity,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'assigned_to': self.assigned_to
        }

class Report:
    """Report data model"""
    
    def __init__(self, title: str, report_type: str, data: Dict):
        self.id = None
        self.title = title
        self.type = report_type
        self.data = data
        self.created_at = datetime.utcnow()
        self.generated_by = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'generated_by': self.generated_by
        }
