from flask import Blueprint, render_template, send_from_directory, current_app, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.modules.audit.models import AuditLog
from app.modules.core.models import Area, Platform, AccessRequest
import os

core_bp = Blueprint("core", __name__, url_prefix="/")

@core_bp.route("/")
@login_required
def index():
    # Role-based Redirection
    if current_user.role != 'administrador':
        return redirect(url_for('catalogo.index'))
        
    try:
        from flask import request
        page = request.args.get('page', 1, type=int)
        
        # 1. Stats Summary
        from app.modules.auth.models import User
        
        areas_count = Area.query.count()
        platforms_total = Platform.query.count()
        users_total = User.query.count()
        pending_total = AccessRequest.query.filter_by(status='Pendiente').count()
        visits_total = db.session.query(db.func.sum(Platform.visits)).scalar() or 0

        # 2. Chart Data: Users per Platform
        platforms = Platform.query.all()
        up_labels = [p.name for p in platforms[:5]]
        up_values = [p.visits for p in platforms[:5]] # Using visits as proxy for demo

        # 3. Chart Data: Users per Area
        areas = Area.query.all()
        ua_labels = [a.name for a in areas[:5]]
        ua_values = [len(a.platforms) for a in areas[:5]] # Density proxy
        ua_colors = [a.color or '#6366f1' for a in areas[:5]]

        # 4. Chart Data: Pending Requests per Platform
        pending_by_platform = db.session.query(Platform.name, db.func.count(AccessRequest.id))\
            .join(AccessRequest, Platform.id == AccessRequest.platform_id)\
            .filter(AccessRequest.status == 'Pendiente')\
            .group_by(Platform.name).all()
        pr_labels = [p[0] for p in pending_by_platform[:5]]
        pr_values = [p[1] for p in pending_by_platform[:5]]

        # 5. Chart Data: Most Visited
        most_visited = Platform.query.order_by(Platform.visits.desc()).limit(5).all()
        
        # 6. Activity Log
        subq = db.session.query(AuditLog.id).order_by(AuditLog.timestamp.desc()).limit(20).subquery()
        pagination = AuditLog.query.filter(AuditLog.id.in_(db.session.query(subq)))\
                             .order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=10)

        return render_template("index.html", 
                             areas_count_num=areas_count,
                             total=platforms_total,
                             total_users=users_total,
                             pending=pending_total,
                             visits_total=visits_total,
                             users_platform_labels=up_labels,
                             users_platform_values=up_values,
                             users_area_labels=ua_labels,
                             users_area_values=ua_values,
                             users_area_colors=ua_colors,
                             pending_platform_labels=pr_labels,
                             pending_platform_values=pr_values,
                             most_visited=most_visited,
                             log_list=pagination.items)
                             
    except Exception as e:
        current_app.logger.error(f"Error en index: {e}")
        return render_template("index.html", activity=[], pagination=None, 
                             areas_count_num=0, total=0, total_users=0, pending=0, visits_total=0,
                             users_platform_labels=[], users_platform_values=[],
                             users_area_labels=[], users_area_values=[], users_area_colors=[],
                             pending_platform_labels=[], pending_platform_values=[],
                             most_visited=[], log_list=[])

@core_bp.route("/catalogo")
@login_required
def catalogo():
    """Vista de Catálogo redirigida al módulo oficial"""
    return redirect(url_for('catalogo.index'))

@core_bp.route("/dashboard-2")
@login_required
@admin_required
def dashboard_2():
    # Keep original or sync similarly if needed
    return redirect(url_for('core.index'))

@core_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Handler oficial de assets migrado al Core Blueprint"""
    try:
        return send_from_directory(os.path.join(current_app.root_path, '../assets'), filename)
    except Exception as e:
        current_app.logger.error(f"Error sirviendo asset {filename}: {e}")
        return "Asset not found", 404

@core_bp.route("/api/stats")
@login_required
def get_stats():
    # Simple API for real-time updates if needed
    return jsonify({"status": "ok"})
