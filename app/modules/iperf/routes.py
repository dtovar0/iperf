from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.modules.iperf.models import IperfTest
from app.modules.iperf.services import IperfService

iperf_bp = Blueprint('iperf', __name__, url_prefix='/iperf')

@iperf_bp.route('/')
@login_required
def index():
    tests = IperfTest.query.order_by(IperfTest.created_at.desc()).all()
    server_running = IperfService.is_server_running()
    return render_template('iperf/index.html', tests=tests, server_running=server_running)

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
