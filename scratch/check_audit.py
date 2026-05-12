import os
import sys

# Add project root to path
sys.path.append('/home/dtovar/bayblade/iperf')

from app import create_app, db
from app.modules.audit.models import AuditLog

from app.modules.audit.services import add_audit_log

app = create_app()
with app.app_context():
    print("Adding test log...")
    add_audit_log("SISTEMA: TEST", module="DEBUG", target="NEXUS", description="Prueba de escritura de auditoría manual", status="success")
    count = AuditLog.query.count()
    print(f"Total AuditLogs after insert: {count}")
    from app.modules.auth.models import User
    u = User.query.filter_by(email='dtovar').first()
    if u:
        print(f"Updating {u.email} role from {u.role} to administrador")
        u.role = 'administrador'
        db.session.commit()
    
    users = User.query.all()
    print("\nUsers in DB:")
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}, Role: {u.role}, Active: {u.is_active}")
