from app import db

class Area(db.Model):
    __tablename__ = 'areas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='box')
    color = db.Column(db.String(100), default='#6366f1')
    status = db.Column(db.String(20), default='Activo')

    @property
    def color_rgb(self):
        """Converts hex color to RGB comma-separated string for CSS variables."""
        hex_color = self.color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        except:
            return "99, 102, 241" # Default Indigo-500

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'status': self.status
        }

class Platform(db.Model):
    __tablename__ = 'platforms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=False)
    direct_link = db.Column(db.String(255))
    icon = db.Column(db.String(50), default='box')
    logo_url = db.Column(db.String(255), nullable=True)
    bg_color = db.Column(db.String(20), default='#6366f1')
    text_color = db.Column(db.String(20), default='#ffffff')
    status = db.Column(db.String(20), default='Activo')
    visits = db.Column(db.Integer, default=0)
    storage_path = db.Column(db.String(255))
    can_download = db.Column(db.Boolean, default=False)
    can_upload = db.Column(db.Boolean, default=False)
    is_encrypted = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(255)) # Encrypted platform password
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Relationships
    area = db.relationship('Area', backref=db.backref('platforms', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'area_id': self.area_id,
            'icon': self.icon,
            'direct_link': self.direct_link,
            'logo_url': self.logo_url,
            'bg_color': self.bg_color,
            'text_color': self.text_color,
            'status': self.status,
            'storage_path': self.storage_path,
            'can_download': self.can_download,
            'can_upload': self.can_upload,
            'is_encrypted': self.is_encrypted,
            'user_ids': [u.id for u in self.users]
        }

class AccessRequest(db.Model):
    __tablename__ = 'access_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    user_email = db.Column(db.String(120), nullable=False) # Linked by email to support Nexus Auth
    status = db.Column(db.String(20), default='Pendiente') 
    created_at = db.Column(db.DateTime, default=db.func.now())
    processed_at = db.Column(db.DateTime)

    # Relationships
    platform = db.relationship('Platform', backref=db.backref('requests', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'platform_id': self.platform_id,
            'user_email': self.user_email,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DriveActivity(db.Model):
    __tablename__ = 'drive_activity'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(512))
    action = db.Column(db.String(50)) # Alta, Baja, Descarga, Carpeta
    file_size = db.Column(db.BigInteger, default=0)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    # Relationships
    user = db.relationship('User', backref=db.backref('drive_activities', lazy=True))
    area = db.relationship('Area', backref=db.backref('drive_activities', lazy=True))
    platform = db.relationship('Platform', backref=db.backref('drive_activities', lazy=True))

class StorageStat(db.Model):
    __tablename__ = 'storage_stats'
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    size_bytes = db.Column(db.BigInteger, default=0)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    platform = db.relationship('Platform', backref=db.backref('storage_stats', lazy=True, cascade="all, delete-orphan"))
