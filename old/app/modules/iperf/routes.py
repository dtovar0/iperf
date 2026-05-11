from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, send_file
from flask_login import login_required, current_user
from app import db
from app.modules.iperf.models import IperfTest, IperfSession, IperfMeasurement, IperfSessionSummary
from app.modules.iperf.services import IperfService
from app.modules.iperf.report import generate_report
import io
import os
from functools import wraps
from datetime import datetime

iperf_bp = Blueprint('iperf', __name__, url_prefix='/iperf')

# ── API Token Security ────────────────────────────────────────────────────────
# Se obtiene de variables de entorno para evitar hardcoding.
API_TOKEN = os.getenv('IPERF_API_TOKEN', 'nexus_default_secret_2024') 

def require_api_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        if not token or token != API_TOKEN:
            return jsonify({"error": "Unauthorized", "message": "Invalid or missing API Token"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ── UI Routes ─────────────────────────────────────────────────────────────────

@iperf_bp.route('/')
@login_required
def index():
    return redirect('/iperf/server')

@iperf_bp.route('/history')
@login_required
def history():
    return redirect('/iperf/history')

@iperf_bp.route('/api/history-list')
@login_required
def history_list():
    # Consultar sesiones terminadas o en curso del usuario
    sessions = IperfSession.query.filter_by(user_id=current_user.id)\
                                 .order_by(IperfSession.started_at.desc()).all()
    
    results = []
    for s in sessions:
        bw = "--"
        if s.summary:
            bw = f"{s.summary.avg_gbps:.2f}"
        
        results.append({
            "id": s.id,
            "status": s.status,
            "protocol": s.protocol.upper(),
            "target_host": s.host or "LOCALHOST",
            "port": s.port,
            "bandwidth": bw,
            "date": s.started_at.strftime('%d/%m/%Y %H:%M:%S') if s.started_at else "--"
        })

    return jsonify({
        "status": "success",
        "tests": results
    })

@iperf_bp.route('/start-server', methods=['POST'])
@login_required
def start_server():
    success, message = IperfService.start_server(current_user.id)
    return jsonify({'success': success, 'message': message})

@iperf_bp.route('/stop-server', methods=['POST'])
@login_required
def stop_server():
    success, message = IperfService.stop_server(current_user.id)
    return jsonify({'success': success, 'message': message})

@iperf_bp.route('/server-status')
@login_required
def server_status():
    return jsonify({'running': IperfService.is_server_running(current_user.id)})

@iperf_bp.route('/server-logs')
@login_required
def server_logs():
    log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"
    if not os.path.exists(log_path):
        return jsonify({'logs': 'No logs found yet.'})
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
        return jsonify({'logs': "".join(lines[-100:])})

@iperf_bp.route('/report/<int:session_id>')
@login_required
def download_report(session_id):
    # Seguridad: Solo el dueño de la sesión o un administrador puede ver el reporte
    session = IperfSession.query.get_or_404(session_id)
    if current_user.role != 'administrador' and session.user_id != current_user.id:
        return "Unauthorized: You do not have permission to view this report.", 403

    measurements = IperfMeasurement.query.filter_by(session_id=session_id).order_by(IperfMeasurement.measured_at.asc()).all()
    
    if not measurements:
        return "No measurement data available for this session.", 404
        
    ts = [m.measured_at.strftime("%H:%M:%S") for m in measurements]
    gbps_vals = [m.gbps for m in measurements]
    jitter_vals = [m.jitter_ms for m in measurements]
    retx_vals = [m.retransmits for m in measurements]
    
    # Preparar session_data plano para el motor de reportes (1:1 Logic)
    session_data = session.to_dict()
    if session.summary:
        summary = session.summary.to_dict()
        session_data.update(summary)
    
    # Asegurar que existan los campos que espera report.py
    session_data['total_retransmits'] = session_data.get('total_retransmits', sum(retx_vals))
    session_data['total_samples'] = session_data.get('total_samples', len(ts))

    pdf_bytes = generate_report(
        session_data,
        ts,
        gbps_vals,
        jitter_vals,
        retx_vals
    )
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'iperf_report_{session_id}.pdf'
    )

@iperf_bp.route('/run', methods=['POST'])
@login_required
def run_test():
    data = request.form
    target_host = data.get('target_host')
    
    if not target_host:
        return jsonify({'error': 'Target host is required'}), 400
        
    new_test = IperfTest(
        target_host=target_host,
        port=int(data.get('port', 5201)),
        duration=int(data.get('duration', 10)),
        protocol=data.get('protocol', 'TCP'),
        user_id=current_user.id
    )
    
    db.session.add(new_test)
    db.session.commit()
    
    # Iniciar asíncronamente
    IperfService.run_test_async(new_test.id, current_app._get_current_object())
    
    return jsonify({
        'message': 'Test started',
        'test_id': new_test.id
    })

@iperf_bp.route('/status/<int:test_id>')
@login_required
def get_status(test_id):
    test = IperfTest.query.get_or_404(test_id)
    return jsonify({
        'id': test.id,
        'status': test.status,
        'finished': test.status in ['completed', 'failed']
    })

@iperf_bp.route('/results/<int:test_id>')
@login_required
def get_results(test_id):
    test = IperfTest.query.get_or_404(test_id)
    return jsonify(test.to_dict())

@iperf_bp.route('/sessions')
@login_required
def list_sessions():
    # Seguridad: Filtrar por usuario actual
    query = IperfSession.query
    if current_user.role != 'administrador':
        query = query.filter_by(user_id=current_user.id)
        
    sessions = query.order_by(IperfSession.started_at.desc()).limit(20).all()
    return jsonify([s.to_dict() for s in sessions])

# ── REST API Endpoints (Parity with test module) ──────────────────────────────

@iperf_bp.route('/api/reports/sessions', methods=['GET'])
@require_api_token
def api_list_sessions():
    """Lista las últimas sesiones con su resumen (formato compatible con test/app.py)."""
    limit = int(request.args.get('limit', 50))
    mode = request.args.get('mode')
    
    query = IperfSession.query
    if mode:
        query = query.filter_by(mode=mode)
    
    sessions = query.order_by(IperfSession.started_at.desc()).limit(limit).all()
    
    results = []
    for s in sessions:
        results.append(s.to_dict())
        
    return jsonify(results)

@iperf_bp.route('/api/reports/sessions/<int:session_id>', methods=['GET'])
@require_api_token
def api_session_detail(session_id):
    """Retorna el resumen y todos los puntos de una sesión específica."""
    session = IperfSession.query.get_or_404(session_id)
    measurements = IperfMeasurement.query.filter_by(session_id=session_id).order_by(IperfMeasurement.measured_at.asc()).all()
    
    meas_list = []
    for m in measurements:
        meas_list.append({
            "measured_at": m.measured_at.isoformat(),
            "gbps": m.gbps,
            "jitter_ms": m.jitter_ms,
            "retransmits": m.retransmits
        })
        
    return jsonify({
        "summary": session.to_dict(),
        "measurements": meas_list
    })

@iperf_bp.route('/api/status', methods=['GET'])
def api_status():
    """Status básico para monitoreo externo."""
    return jsonify({
        "status": "online",
        "server_running": IperfService.is_server_running(),
        "timestamp": datetime.now().isoformat()
    })
