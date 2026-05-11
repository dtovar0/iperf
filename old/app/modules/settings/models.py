from app import db
from datetime import datetime

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    portal_name = db.Column(db.String(100), default='Nexus Core AI')
    portal_identity_type = db.Column(db.String(10), default='icon') # 'icon' or 'image'
    portal_icon = db.Column(db.Text, nullable=True) # Storing SVG code or Image DataURL/Path
    bg_color = db.Column(db.String(20), default='#0f172a')

    text_color = db.Column(db.String(20), default='#ffffff')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "portal_name": self.portal_name,
            "portal_identity_type": self.portal_identity_type,
            "portal_icon": self.portal_icon,

            "bg_color": self.bg_color,
            "text_color": self.text_color
        }
