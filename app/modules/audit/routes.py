from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required, current_user
from app.decorators import admin_required
from .models import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
@admin_required
def index():
    try:
        return render_template('audit.html')
    except Exception as e:
        current_app.logger.error(f"Error en audit.index: {e}")
        return render_template('errors/500.html'), 500

@audit_bp.route('/api/list')
@login_required
@admin_required
def list_audit():
    try:
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(500).all()
        
        return jsonify({
            "status": "success",
            "logs": [log.to_dict() for log in logs]
        })
    except Exception as e:
        current_app.logger.error(f"Error en list_audit: {e}")
        return jsonify({"status": "error", "message": "No se pudo obtener el historial de auditoría"}), 500
