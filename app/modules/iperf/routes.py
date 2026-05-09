from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, send_file
from flask_login import login_required, current_user
from app import db
from app.modules.iperf.models import IperfTest, IperfSession, IperfMeasurement, IperfSessionSummary
from app.modules.iperf.services import IperfService
from app.modules.iperf.report import generate_report
import io

iperf_bp = Blueprint('iperf', __name__, url_prefix='/iperf')

@iperf_bp.route('/')
@login_required
def index():
    return redirect('/iperf/dashboard/')

@iperf_bp.route('/start-server', methods=['POST'])
@login_required
def start_server():
    success, message = IperfService.start_server()
    return jsonify({'success': success, 'message': message})

@iperf_bp.route('/stop-server', methods=['POST'])
@login_required
def stop_server():
    success, message = IperfService.stop_server()
    return jsonify({'success': success, 'message': message})

@iperf_bp.route('/server-status')
@login_required
def server_status():
    return jsonify({'running': IperfService.is_server_running()})

@iperf_bp.route('/server-logs')
@login_required
def server_logs():
    import os
    log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"
    if not os.path.exists(log_path):
        return jsonify({'logs': 'No logs found yet.'})
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
        return jsonify({'logs': "".join(lines[-100:])})

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
    sessions = IperfSession.query.order_by(IperfSession.started_at.desc()).limit(20).all()
    return jsonify([s.to_dict() for s in sessions])

@iperf_bp.route('/report/<int:session_id>')
@login_required
def download_report(session_id):
    session = IperfSession.query.get_or_404(session_id)
    measurements = IperfMeasurement.query.filter_by(session_id=session_id).order_by(IperfMeasurement.measured_at.asc()).all()
    
    if not measurements:
        return "No measurement data available for this session.", 404
        
    ts = [m.measured_at.strftime("%H:%M:%S") for m in measurements]
    gbps_vals = [m.gbps for m in measurements]
    jitter_vals = [m.jitter_ms for m in measurements]
    retx_vals = [m.retransmits for m in measurements]
    
    pdf_bytes = generate_report(
        session.to_dict(),
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
