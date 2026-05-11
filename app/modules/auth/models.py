from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Helper Table for Platform-User Relationship (Favs/Access)
user_platforms = db.Table('user_platforms',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('platform_id', db.Integer, db.ForeignKey('platforms.id'), primary_key=True)
)

# Helper Table for User Favorites
user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('platform_id', db.Integer, db.ForeignKey('platforms.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=True) # Nombre visible del usuario
    password_hash = db.Column(db.String(255), nullable=True) # Nulo para usuarios LDAP
    role = db.Column(db.String(20), default='usuario') # administrador, usuario
    auth_source = db.Column(db.String(10), default='local') # local, ldap
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    platforms = db.relationship('Platform', secondary='user_platforms', backref=db.backref('users', lazy='dynamic'))
    favorites = db.relationship('Platform', secondary='user_favorites', backref=db.backref('favorited_by', lazy='dynamic'))

    # User Interface Preferences
    pref_notifications = db.Column(db.Boolean, default=True)
    pref_email_notifications = db.Column(db.Boolean, default=True)
    pref_refresh_interval = db.Column(db.Integer, default=60)
    pref_tour_enabled = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AuthConfig(db.Model):
    __tablename__ = 'auth_config'
    
    id = db.Column(db.Integer, primary_key=True)
    ldap_host = db.Column(db.String(100), nullable=True)
    ldap_port = db.Column(db.Integer, default=389)
    ldap_ssl = db.Column(db.Boolean, default=False)
    ldap_base_dn = db.Column(db.String(200), nullable=True)
    ldap_user = db.Column(db.String(100), nullable=True)
    ldap_pass = db.Column(db.String(100), nullable=True)
    ldap_user_attr = db.Column(db.String(50), default='sAMAccountName')
    
    # Role Mapping (LDAP Groups)
    ldap_group_admin = db.Column(db.String(200), nullable=True)
    ldap_group_user = db.Column(db.String(200), nullable=True)
    ldap_role_mappings = db.Column(db.Text, nullable=True) # JSON string for dynamic mappings
    
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "ldap_host": self.ldap_host,
            "ldap_port": self.ldap_port,
            "ldap_ssl": self.ldap_ssl,
            "ldap_base_dn": self.ldap_base_dn,
            "ldap_user": self.ldap_user,
            "ldap_user_attr": self.ldap_user_attr,
            "ldap_group_admin": self.ldap_group_admin,
            "ldap_group_user": self.ldap_group_user,
            "ldap_role_mappings": self.ldap_role_mappings
        }
