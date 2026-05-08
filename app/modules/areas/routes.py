from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.modules.core.models import Area, Platform
from app.modules.auth.models import User
from app.modules.audit.models import AuditLog
import json

areas_bp = Blueprint('areas_module', __name__, url_prefix='/admin/areas')

@areas_bp.route('/')
@login_required
@admin_required
def areas_list():
    areas = Area.query.all()
    users = User.query.filter_by(is_active=True).all()
    
    # Adapt data for JS
    areas_data = []
    for a in areas:
        areas_data.append({
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'icon': a.icon,
            'color': a.color,
            'status': a.status,
            'users_count': len(a.users) if hasattr(a, 'users') else 0,
            'platforms_count': len(a.platforms) if hasattr(a, 'platforms') else 0
        })
    
    users_data = [{'id': u.id, 'name': u.nombre or u.email, 'email': u.email} for u in users]
    
    return render_template('areas.html', 
                         areas_json=areas_data, 
                         all_users_json=users_data)

@areas_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add_area():
    try:
        data = request.get_json()
        name = data.get('name')
        
        if Area.query.filter_by(name=name).first():
            return jsonify({'status': 'error', 'message': 'El nombre del área ya existe'}), 400
            
        new_area = Area(
            name=name,
            description=data.get('description'),
            icon=data.get('icon', 'box'),
            color=data.get('color', '#6366f1'),
            status=data.get('status', 'Activo')
        )
        
        # Link users if provided
        user_ids = data.get('user_ids', [])
        if user_ids:
            users = User.query.filter(User.id.in_(user_ids)).all()
            new_area.users = users
            
        db.session.add(new_area)
        
        # Audit Log
        log = AuditLog(
            user=current_user.email,
            action='Alta',
            module='Áreas',
            target=name,
            description=f"Nueva área creada: {name}",
            status='success'
        )
        db.session.add(log)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Área creada correctamente'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding area: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@areas_bp.route('/edit/<int:area_id>', methods=['POST'])
@login_required
@admin_required
def edit_area(area_id):
    try:
        area = Area.query.get_or_404(area_id)
        data = request.get_json()
        
        # Check name uniqueness if changed
        new_name = data.get('name')
        if new_name != area.name and Area.query.filter_by(name=new_name).first():
            return jsonify({'status': 'error', 'message': 'El nombre del área ya existe'}), 400
            
        area.name = new_name
        area.description = data.get('description')
        area.icon = data.get('icon')
        area.color = data.get('color')
        area.status = data.get('status')
        
        # Update users
        user_ids = data.get('user_ids', [])
        users = User.query.filter(User.id.in_(user_ids)).all()
        area.users = users
        
        # Audit Log
        log = AuditLog(
            user=current_user.email,
            action='Modificación',
            module='Áreas',
            target=area.name,
            description=f"Área actualizada: {area.name}",
            status='success'
        )
        db.session.add(log)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Área actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing area: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@areas_bp.route('/delete/<int:area_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_area(area_id):
    try:
        area = Area.query.get_or_404(area_id)
        area_name = area.name
        
        # Check if platforms are linked
        if area.platforms:
             return jsonify({'status': 'error', 'message': 'No se puede eliminar el área porque tiene plataformas vinculadas'}), 400
             
        db.session.delete(area)
        
        # Audit Log
        log = AuditLog(
            user=current_user.email,
            action='Baja',
            module='Áreas',
            target=area_name,
            description=f"Área eliminada: {area_name}",
            status='success'
        )
        db.session.add(log)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Área eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting area: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@areas_bp.route('/delete-bulk', methods=['POST'])
@login_required
@admin_required
def delete_areas_bulk():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return jsonify({'status': 'error', 'message': 'No se proporcionaron IDs'}), 400
            
        areas = Area.query.filter(Area.id.in_(ids)).all()
        
        # Check for dependencies first
        restricted_areas = [a.name for a in areas if a.platforms]
        if restricted_areas:
            names = ", ".join(restricted_areas)
            return jsonify({
                'status': 'error', 
                'message': f'No se pueden eliminar las siguientes áreas porque tienen plataformas vinculadas: {names}. Primero debes eliminar o reasignar sus plataformas.'
            }), 400
            
        deleted_count = 0
        for area in areas:
            area_name = area.name
            db.session.delete(area)
            
            log = AuditLog(
                user=current_user.email,
                action='Baja',
                module='Áreas',
                target=area_name,
                description=f"Área eliminada (Bulk): {area_name}",
                status='success'
            )
            db.session.add(log)
            deleted_count += 1
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{deleted_count} áreas eliminadas correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@areas_bp.route('/users/<int:area_id>')
@login_required
@admin_required
def get_area_users(area_id):
    try:
        area = Area.query.get_or_404(area_id)
        selected_ids = [u.id for u in area.users]
        return jsonify({'status': 'success', 'selected_ids': selected_ids})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
