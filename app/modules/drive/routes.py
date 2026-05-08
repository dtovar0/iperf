from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify, request, send_file
from flask_login import login_required, current_user
from app.modules.core.models import Area, Platform, DriveActivity, StorageStat
from app.modules.auth.models import User
from app import db
from .utils import StorageManager, SecretManager, log_drive_activity
import os
import math
from datetime import datetime

drive_bp = Blueprint('drive', __name__, url_prefix='/drive')

def _resolve_platform_access(path):
    # Obtener todas las plataformas permitidas
    allowed_platforms = Platform.query.all() if current_user.role.lower() == 'administrador' else current_user.platforms
    
    # Normalizar el path solicitado
    norm_path = os.path.normpath(path)
    
    for p in allowed_platforms:
        # Resolver el path físico de la plataforma
        p_path = StorageManager.get_safe_path(p.storage_path or p.name)
        if norm_path.startswith(p_path):
            return p
    
    # Si no tiene acceso a ninguna y no es admin, fuera.
    if current_user.role.lower() != 'administrador':
        raise PermissionError('No tienes acceso a esta ubicación.')
    return None

def _validate_platform_password(target_platform, password):
    if target_platform and target_platform.is_encrypted and target_platform.password:
        decrypted_pass = SecretManager.decrypt(target_platform.password)
        if password != decrypted_pass:
            raise PermissionError('Contraseña incorrecta')

def _resolve_area_root(path):
    for area in Area.query.all():
        area_path = StorageManager.get_safe_path(area.name)
        if path == area_path:
            return area
    return None

def _ensure_not_area_root_action(path, action_label):
    area = _resolve_area_root(path)
    if area:
        raise PermissionError(f'No puedes {action_label} directamente en la raíz del área "{area.name}".')

@drive_bp.route('/')
@login_required
def index():
    try:
        user = current_user
        if user.role.lower() == 'administrador':
            approved_areas = Area.query.order_by(Area.name).all()
            approved_platforms = Platform.query.all()
        else:
            approved_areas = [a for a in user.areas if a.status == 'Activo']
            approved_platforms = user.platforms
            
        return render_template('drive.html', 
                               approved_areas=approved_areas, 
                               approved_platforms=approved_platforms,
                               platforms_json=[p.to_dict() for p in approved_platforms])
    except Exception as e:
        current_app.logger.error(f"Error en Drive Index: {e}")
        return render_template('errors/500.html'), 500

@drive_bp.route('/api/drive/list', methods=['GET', 'POST'])
@login_required
def list_files_api():
    try:
        data = (request.is_json and request.get_json()) or {}
        requested_path = data.get('path') or request.args.get('path') or ''
        
        if not requested_path or requested_path in ['', '/']:
            platforms = Platform.query.order_by(Platform.name).all() if current_user.role.lower() == 'administrador' else current_user.platforms
            if platforms:
                requested_path = platforms[0].storage_path or platforms[0].name
            else:
                return jsonify({'success': False, 'error': 'No tienes accesos activos.'}), 403

        path = StorageManager.get_safe_path(requested_path)
        
        if not os.path.exists(path):
            try: os.makedirs(path, exist_ok=True)
            except: return jsonify({'success': False, 'error': f'Ruta inaccesible: {requested_path}'}), 404
            
        target_platform = _resolve_platform_access(path)
        area_root = _resolve_area_root(path)

        def get_human_size(size_bytes):
            if size_bytes == 0: return "0 B"
            units = ("B", "KB", "MB", "GB", "TB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {units[i]}"

        items = []
        for entry in os.scandir(path):
            if entry.name == '.nexus_lock': continue
            try:
                stats = entry.stat()
                items.append({
                    'name': entry.name,
                    'is_dir': entry.is_dir(),
                    'size': get_human_size(stats.st_size) if not entry.is_dir() else '--',
                    'mtime': stats.st_mtime,
                    'ctime': stats.st_ctime,
                    'path': requested_path.rstrip('/') + '/' + entry.name
                })
            except: continue 
        
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        return jsonify({
            'success': True,
            'items': items,
            'protected': target_platform.is_encrypted if target_platform else False,
            'current_path': requested_path,
            'permissions': {
                'can_download': target_platform.can_download if target_platform else True,
                'can_upload': target_platform.can_upload if target_platform else True
            },
            'context': {
                'kind': 'area_root' if area_root and not target_platform else 'platform',
                'area_name': area_root.name if area_root else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@drive_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se encontró el archivo'}), 400
            
        file = request.files['file']
        path_str = request.form.get('path')
        password = request.form.get('password')
        
        if not StorageManager.is_safe_file(file.filename):
            return jsonify({'success': False, 'error': 'Tipo de archivo no permitido.'}), 400
            
        safe_filename = StorageManager.sanitize_filename(file.filename)
        dest_dir = StorageManager.get_safe_path(path_str)
        _ensure_not_area_root_action(dest_dir, 'subir archivos')
        target_platform = _resolve_platform_access(dest_dir)
        
        if target_platform:
            if not target_platform.can_upload:
                return jsonify({'success': False, 'error': 'Subidas deshabilitadas'}), 403
            _validate_platform_password(target_platform, password)

        full_path = os.path.join(dest_dir, safe_filename)
        if os.path.exists(full_path):
            return jsonify({'success': False, 'error': f'El archivo "{safe_filename}" ya existe.'}), 409

        file.save(full_path)
        file_size = os.path.getsize(full_path)
        area_id = target_platform.area_id if target_platform else None
        platform_id = target_platform.id if target_platform else None
        log_drive_activity(safe_filename, path_str, 'Alta', current_user.id, file_size, area_id, platform_id)

        return jsonify({'success': True, 'message': 'Archivo subido correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@drive_bp.route('/api/download', methods=['GET', 'POST'])
@login_required
def download_file():
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            requested_path = data.get('path')
            password = data.get('password')
        else:
            requested_path = request.args.get('path')
            password = request.args.get('password')

        path = StorageManager.get_safe_path(requested_path)
        if not os.path.exists(path):
            return "Archivo no encontrado", 404

        target_platform = _resolve_platform_access(path)
        if target_platform:
            if not target_platform.can_download:
                return "Descargas deshabilitadas", 403
            _validate_platform_password(target_platform, password)

        file_size = os.path.getsize(path)
        area_id = target_platform.area_id if target_platform else None
        platform_id = target_platform.id if target_platform else None
        log_drive_activity(os.path.basename(path), requested_path, 'Descarga', current_user.id, file_size, area_id, platform_id)

        return send_file(path, as_attachment=True)
    except Exception as e:
        return str(e), 500

@drive_bp.route('/api/delete-item', methods=['POST'])
@login_required
def delete_item():
    try:
        data = request.get_json() or {}
        path = StorageManager.get_safe_path(data.get('path'))
        password = data.get('password')
        
        target_platform = _resolve_platform_access(path)
        _validate_platform_password(target_platform, password)
            
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        else:
            os.remove(path)
        
        log_drive_activity(os.path.basename(path), os.path.dirname(path), 'Baja', current_user.id, 0, target_platform.area_id if target_platform else None, target_platform.id if target_platform else None)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@drive_bp.route('/api/create-folder', methods=['POST'])
@login_required
def create_folder():
    try:
        data = request.get_json() or {}
        base_path = StorageManager.get_safe_path(data.get('path'))
        folder_name = data.get('folder_name')
        password = data.get('password')
        
        target_platform = _resolve_platform_access(base_path)
        _validate_platform_password(target_platform, password)
        
        sanitized_name = StorageManager.sanitize_filename(folder_name)
        new_path = os.path.join(base_path, sanitized_name)
        
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': 'La carpeta ya existe'})
            
        os.makedirs(new_path)
        log_drive_activity(sanitized_name, data.get('path'), 'Carpeta', current_user.id, 0, target_platform.area_id if target_platform else None, target_platform.id if target_platform else None)
        return jsonify({'success': True, 'sanitized_name': sanitized_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@drive_bp.route('/api/drive-logs')
@login_required
def get_drive_logs():
    try:
        logs = DriveActivity.query.order_by(DriveActivity.created_at.desc()).limit(6).all()
        return jsonify({
            'success': True, 
            'logs': [{
                'user_name': l.user.name if l.user else 'Sistema',
                'target_name': l.file_name,
                'action': l.action,
                'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for l in logs]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@drive_bp.route('/api/drive/stats')
@login_required
def get_drive_stats():
    try:
        areas_count = Area.query.count() if current_user.role.lower() == 'administrador' else len(current_user.areas)
        plats_count = Platform.query.count() if current_user.role.lower() == 'administrador' else len(current_user.platforms)
        
        base_query = DriveActivity.query
        if current_user.role.lower() != 'administrador':
            base_query = base_query.filter_by(user_id=current_user.id)

        downloads_count = base_query.filter_by(action='Descarga').count()
        uploads_count = base_query.filter(DriveActivity.action.in_(['Alta', 'Carga'])).count()

        return jsonify({
            'success': True, 
            'kpis': {
                'areas': areas_count,
                'platforms': plats_count,
                'downloads': downloads_count,
                'uploads': uploads_count
            },
            'charts': {
                'downloads': {'labels': [], 'values': []},
                'uploads': {'labels': [], 'values': []}
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
