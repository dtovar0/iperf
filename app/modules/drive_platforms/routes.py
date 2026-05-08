from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.modules.core.models import Area, Platform
from app.modules.auth.models import User
from app.modules.audit.models import AuditLog
from app.modules.drive.utils import SecretManager, StorageManager, log_drive_activity
import os
import json

drive_platforms_bp = Blueprint('drive_platforms', __name__, url_prefix='/admin/drive-platforms')

@drive_platforms_bp.route('/')
@login_required
@admin_required
def index():
    # Solo mostramos plataformas que tienen storage_path (Unidades de Drive)
    # Opcionalmente, podemos filtrar por un campo 'is_drive_unit' si lo añadimos después.
    # Por ahora usamos el filtro de storage_path.
    drive_units = Platform.query.filter(Platform.storage_path.isnot(None)).all()
    areas = Area.query.all()
    users = User.query.filter_by(is_active=True).all()
    
    users_data = [{'id': u.id, 'name': u.nombre or u.email, 'email': u.email} for u in users]
    areas_data = [{'id': a.id, 'name': a.name} for a in areas]
    
    units_json = []
    for u in drive_units:
        units_json.append({
            'id': u.id,
            'name': u.name,
            'description': u.description,
            'area_id': u.area_id,
            'area_name': u.area.name if u.area else 'N/A',
            'storage_path': u.storage_path,
            'icon': u.icon or 'fa-folder',
            'can_download': u.can_download,
            'can_upload': u.can_upload,
            'is_encrypted': u.is_encrypted,
            'status': u.status,
            'user_ids': [user.id for user in u.users]
        })

    return render_template('drive_platforms.html', 
                           units=drive_units, 
                           units_json=units_json,
                           areas=areas_data,
                           all_users=users_data)

@drive_platforms_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add_unit():
    try:
        data = request.form
        name = data.get('name')
        area_id = data.get('area_id')
        
        area = Area.query.get(area_id)
        if not area:
            return jsonify({'success': False, 'error': 'Área no válida'}), 400
            
        # Generar storage_path automático
        storage_path = os.path.join(area.name, name)
        
        new_unit = Platform(
            name=name,
            description=data.get('description'),
            area_id=area_id,
            storage_path=storage_path,
            icon=data.get('icon', 'fa-folder'),
            can_download=data.get('can_download') == 'true',
            can_upload=data.get('can_upload') == 'true',
            is_encrypted=data.get('is_encrypted') == 'true',
            status='Activo'
        )
        
        password = data.get('password')
        if password and new_unit.is_encrypted:
            new_unit.password = SecretManager.encrypt(password)
            
        # Crear Carpeta Física
        try:
            full_path = StorageManager.get_safe_path(storage_path)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
        except Exception as e:
            current_app.logger.error(f"Error creando directorio de drive: {e}")

        db.session.add(new_unit)
        db.session.flush()

        # Asignar Usuarios
        user_ids = data.get('users')
        if user_ids:
            ids = json.loads(user_ids)
            users = User.query.filter(User.id.in_(ids)).all()
            new_unit.users = users

        # Log
        log = AuditLog(
            user=current_user.email,
            action='Alta',
            module='Drive Units',
            target=name,
            description=f"Nueva unidad de Drive creada: {name}",
            status='success'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Unidad de Drive creada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@drive_platforms_bp.route('/edit/<int:unit_id>', methods=['POST'])
@login_required
@admin_required
def edit_unit(unit_id):
    try:
        unit = Platform.query.get_or_404(unit_id)
        data = request.form
        
        unit.name = data.get('name')
        unit.description = data.get('description')
        unit.area_id = data.get('area_id')
        unit.icon = data.get('icon', 'fa-folder')
        unit.can_download = data.get('can_download') == 'true'
        unit.can_upload = data.get('can_upload') == 'true'
        unit.is_encrypted = data.get('is_encrypted') == 'true'
        
        password = data.get('password')
        if password and unit.is_encrypted:
            unit.password = SecretManager.encrypt(password)
            
        # Actualizar storage_path si es necesario
        area = Area.query.get(unit.area_id)
        if area:
            unit.storage_path = os.path.join(area.name, unit.name)

        # Asignar Usuarios
        user_ids = data.get('users')
        if user_ids:
            ids = json.loads(user_ids)
            users = User.query.filter(User.id.in_(ids)).all()
            unit.users = users

        db.session.commit()
        return jsonify({'success': True, 'message': 'Unidad actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@drive_platforms_bp.route('/delete/<int:unit_id>', methods=['POST'])
@login_required
@admin_required
def delete_unit(unit_id):
    try:
        unit = Platform.query.get_or_404(unit_id)
        # Nota: No borramos la carpeta física por seguridad (solo el registro)
        db.session.delete(unit)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
