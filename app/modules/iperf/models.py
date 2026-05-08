from app import db
from datetime import datetime
import json

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
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'results': json.loads(self.results_json) if self.results_json else None
        }
