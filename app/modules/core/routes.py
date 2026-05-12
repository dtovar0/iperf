from flask import Blueprint, render_template, send_from_directory, current_app, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.modules.audit.models import AuditLog
from app.modules.iperf.models import IperfSession, IperfServerConfig
import os

core_bp = Blueprint("core", __name__, url_prefix="/")

@core_bp.route("/")
@login_required
def index():
    # Role-based Redirection
    if current_user.role != 'administrador':
        return redirect(url_for('iperf.index'))
        
    try:
        from flask import request
        page = request.args.get('page', 1, type=int)
        
        # 1. Stats Summary
        from app.modules.auth.models import User
        
        users_total = User.query.count()
        users_active = User.query.filter_by(is_active=True).count()
        servers_count = IperfServerConfig.query.count()
        client_tests = IperfSession.query.filter_by(mode='client').count()
        server_tests = IperfSession.query.filter_by(mode='server').count()
        
        # 2. Chart: Tests Cliente por Usuario
        client_user_data = db.session.query(User.nombre, db.func.count(IperfSession.id))\
            .join(IperfSession, User.id == IperfSession.user_id)\
            .filter(IperfSession.mode == 'client')\
            .group_by(User.nombre).limit(5).all()
        cu_labels = [u[0] or 'Anónimo' for u in client_user_data]
        cu_values = [u[1] for u in client_user_data]

        # 3. Chart: Tests Servidor por Usuario
        server_user_data = db.session.query(User.nombre, db.func.count(IperfSession.id))\
            .join(IperfSession, User.id == IperfSession.user_id)\
            .filter(IperfSession.mode == 'server')\
            .group_by(User.nombre).limit(5).all()
        su_labels = [u[0] or 'Anónimo' for u in server_user_data]
        su_values = [u[1] for u in server_user_data]

        # 4. Chart: IPs por Usuario (Top Hosts)
        ip_data = db.session.query(IperfSession.host, db.func.count(IperfSession.id))\
            .filter(IperfSession.host != None)\
            .group_by(IperfSession.host).order_by(db.func.count(IperfSession.id).desc()).limit(10).all()
        ip_labels = [i[0] for i in ip_data]
        ip_values = [i[1] for i in ip_data]

        # 5. Chart: Tareas (Trend last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=6)
        trend_query = db.session.query(
            db.func.date(IperfSession.started_at).label('date'),
            IperfSession.mode,
            db.func.count(IperfSession.id)
        ).filter(IperfSession.started_at >= seven_days_ago)\
         .group_by('date', IperfSession.mode).all()
        
        # Prepare trend data
        dates = [(datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        client_trend = {d: 0 for d in dates}
        server_trend = {d: 0 for d in dates}
        
        for row in trend_query:
            d_str = str(row[0])
            if d_str in client_trend:
                if row[1] == 'client': client_trend[d_str] = row[2]
                else: server_trend[d_str] = row[2]
        
        trend_labels = dates
        trend_client = [client_trend[d] for d in dates]
        trend_server = [server_trend[d] for d in dates]

        # 6. Activity Log (Last 20 records)
        log_list = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(20).all()

        return render_template("index.html", 
                             total_users=users_total,
                             users_active=users_active,
                             servers_count=servers_count,
                             client_tests=client_tests,
                             server_tests=server_tests,
                             cu_labels=cu_labels, cu_values=cu_values,
                             su_labels=su_labels, su_values=su_values,
                             ip_labels=ip_labels, ip_values=ip_values,
                             trend_labels=trend_labels, trend_client=trend_client, trend_server=trend_server,
                             log_list=log_list)
                             
    except Exception as e:
        current_app.logger.error(f"Error en index: {e}")
        return render_template("index.html", 
                             total_users=0, users_active=0, servers_count=0, 
                             client_tests=0, server_tests=0, log_list=[],
                             cu_labels=[], cu_values=[],
                             su_labels=[], su_values=[],
                             ip_labels=[], ip_values=[],
                             trend_labels=[], trend_client=[], trend_server=[])

@core_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Handler oficial de assets migrado al Core Blueprint"""
    try:
        return send_from_directory(os.path.join(current_app.root_path, '../assets'), filename)
    except Exception as e:
        current_app.logger.error(f"Error sirviendo asset {filename}: {e}")
        return "Asset not found", 404
