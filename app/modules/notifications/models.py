from app import db
from datetime import datetime

class SMTPConfig(db.Model):
    __tablename__ = 'smtp_config'
    
    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String(100), default='smtp.gmail.com')
    port = db.Column(db.Integer, default=587)
    encryption = db.Column(db.String(20), default='starttls')
    auth_enabled = db.Column(db.Boolean, default=True)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True) # Should be encrypted in production
    sender_name = db.Column(db.String(100), default='Nexus System')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "server": self.server,
            "port": self.port,
            "encryption": self.encryption,
            "auth_enabled": self.auth_enabled,
            "username": self.username,
            "sender_name": self.sender_name
        }

class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_html = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "is_html": self.is_html,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class InAppNotification(db.Model):
    __tablename__ = 'in_app_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # NULL means global
    type = db.Column(db.String(20), default='info') # success, error, warning, info
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "time": self.human_time(),
            "timestamp": self.created_at.isoformat()
        }
    
    def human_time(self):
        now = datetime.now()
        diff = now - self.created_at
        if diff.days > 0: return f"Hace {diff.days} d"
        if diff.seconds > 3600: return f"Hace {diff.seconds // 3600} h"
        if diff.seconds > 60: return f"Hace {diff.seconds // 60} m"
        return "Ahora"

