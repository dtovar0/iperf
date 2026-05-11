from app import db
from app.modules.audit.models import AuditLog
from flask import request
from flask_login import current_user

def add_audit_log(action, status='info', detail=None, user_override=None):
    """
    Registra un evento en la tabla de auditoría.
    """
    try:
        user_name = user_override or (current_user.email if current_user.is_authenticated else 'SYSTEM')
        
        # Intentar obtener IP, si falla es porque es un proceso interno (Backend)
        ip = 'INTERNAL'
        try:
            from flask import has_request_context
            if has_request_context():
                ip = request.remote_addr
        except:
            pass

        log = AuditLog(
            user=user_name,
            action=action,
            status=status,
            detail=detail,
            ip_address=ip
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"❌ Error al escribir en AuditLog: {e}")
        db.session.rollback()
