from app import db
from datetime import datetime
import json

class IperfSession(db.Model):
    __tablename__ = 'iperf_sessions'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    mode = db.Column(db.Enum('server', 'client'), nullable=False)
    host = db.Column(db.String(64), nullable=True)
    port = db.Column(db.Integer, nullable=False, default=5201)
    protocol = db.Column(db.Enum('tcp', 'udp'), nullable=False, default='tcp')
    parallel = db.Column(db.Integer, nullable=False, default=1)
    duration_s = db.Column(db.Integer, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum('running', 'completed', 'aborted'), nullable=False, default='running')
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    measurements = db.relationship('IperfMeasurement', backref='session', lazy=True, cascade="all, delete-orphan")
    summary = db.relationship('IperfSessionSummary', backref='session', uselist=False, lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'mode': self.mode,
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'parallel': self.parallel,
            'duration_s': self.duration_s,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'ended_at': self.ended_at.strftime('%Y-%m-%d %H:%M:%S') if self.ended_at else None,
            'status': self.status,
            'summary': self.summary.to_dict() if self.summary else None
        }

class IperfMeasurement(db.Model):
    __tablename__ = 'iperf_measurements'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    session_id = db.Column(db.BigInteger, db.ForeignKey('iperf_sessions.id', ondelete='CASCADE'), nullable=False)
    measured_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    gbps = db.Column(db.Float, nullable=False)
    jitter_ms = db.Column(db.Float, nullable=False, default=0)
    retransmits = db.Column(db.Integer, nullable=False, default=0)

class IperfSessionSummary(db.Model):
    __tablename__ = 'iperf_session_summary'
    
    session_id = db.Column(db.BigInteger, db.ForeignKey('iperf_sessions.id', ondelete='CASCADE'), primary_key=True)
    avg_gbps = db.Column(db.Float, nullable=False)
    max_gbps = db.Column(db.Float, nullable=False)
    min_gbps = db.Column(db.Float, nullable=False)
    avg_jitter_ms = db.Column(db.Float, nullable=False, default=0)
    total_retransmits = db.Column(db.Integer, nullable=False, default=0)
    total_samples = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'avg_gbps': self.avg_gbps,
            'max_gbps': self.max_gbps,
            'min_gbps': self.min_gbps,
            'avg_jitter_ms': self.avg_jitter_ms,
            'total_retransmits': self.total_retransmits,
            'total_samples': self.total_samples
        }

class IperfTest(db.Model):
    __tablename__ = 'iperf_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    target_host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, default=5201)
    duration = db.Column(db.Integer, default=10)
    protocol = db.Column(db.String(10), default='TCP') # TCP, UDP
    status = db.Column(db.String(50), default='pending') # pending, running, completed, failed
    
    results_json = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'target_host': self.target_host,
            'port': self.port,
            'duration': self.duration,
            'protocol': self.protocol,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'results': json.loads(self.results_json) if self.results_json else None
        }


class IperfServerConfig(db.Model):
    """Configuración de servidores iperf3 remotos para pruebas de red."""
    __tablename__ = 'iperf_server_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'host': self.host,
            'token': self.token or '',
            'status': 'Activo' if self.is_active else 'Inactivo',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
