from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.modules.core.models import Area, Platform
from app.modules.auth.models import User
from app.modules.audit.models import AuditLog
import os

platforms_bp = Blueprint('platforms_module', __name__, url_prefix='/admin/platforms')

@platforms_bp.route('/')
@login_required
@admin_required
def platforms_list():
    platforms = Platform.query.all()
    areas = Area.query.all()
    users = User.query.filter_by(is_active=True).all()
    
    # Adapt data for JS (1:1 with legacy expectation)
    area_list = []
    for a in areas:
        area_list.append({
            'id': a.id,
            'name': a.name,
            'icon': a.icon or 'box',
            'color': a.color or '#6366f1',
            'status': a.status
        })

    grouped_platforms = {}
    for a in areas:
        area_platforms = [p for p in platforms if p.area_id == a.id]
        grouped_platforms[str(a.id)] = [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'area_id': p.area_id,
            'direct_link': p.direct_link,
            'icon': p.icon,
            'status': p.status,
            'users_count': p.users.count() if hasattr(p, 'users') else 0,
            'bg_color': p.bg_color or '#6366f1',
            'text_color': getattr(p, 'text_color', '#ffffff'),
            'logo_url': p.logo_url,
            'user_ids': [u.id for u in p.users] if hasattr(p, 'users') else []
        } for p in area_platforms]

    users_data = [{'id': u.id, 'name': u.nombre or u.email, 'email': u.email} for u in users]
    
    # Flatten version for some existing logic
    platforms_flat = []
    for p in platforms:
        platforms_flat.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'area_id': p.area_id,
            'area_name': p.area.name if p.area else 'N/A',
            'direct_link': p.direct_link,
            'icon': p.icon,
            'status': p.status,
            'users_count': p.users.count() if hasattr(p, 'users') else 0,
            'user_ids': [u.id for u in p.users] if hasattr(p, 'users') else []
        })

    return render_template('platforms.html', 
                         grouped_platforms=grouped_platforms,
                         area_list=area_list,
                         all_users=users_data,
                         platforms_json=platforms_flat,
                         areas=areas)

@platforms_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add_platform():
    try:
        name = request.form.get('name')
        area_id = request.form.get('area_id')
        description = request.form.get('description')
        
        if not area_id or area_id == 'null' or area_id == 'undefined':
            return jsonify({'success': False, 'error': 'El Área es obligatoria. No puede existir una plataforma sin área asignada.'}), 400
            
        direct_link = request.form.get('direct_link')
        icon = request.form.get('icon', 'box')
        status = request.form.get('status', 'Activo')
        bg_color = request.form.get('bg_color', '#6366f1')
        text_color = request.form.get('text_color', '#ffffff')
        
        new_platform = Platform(
            name=name,
            description=description,
            area_id=area_id,
            direct_link=direct_link,
            icon=icon,
            status=status,
            bg_color=bg_color,
            text_color=text_color
        )
        
        # Handle Logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                filename = f"plat_{name.lower().replace(' ', '_')}_{file.filename}"
                upload_path = os.path.join(current_app.root_path, '../assets/img/platforms', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                new_platform.logo_url = f"/assets/img/platforms/{filename}"

        db.session.add(new_platform)
        db.session.flush() # Get ID for relationships

        # Handle Users
        user_ids = request.form.get('users')
        if user_ids:
            import json
            ids = json.loads(user_ids)
            users = User.query.filter(User.id.in_(ids)).all()
            new_platform.users = users

        # Audit Log
        log = AuditLog(
            user=current_user.email,
            action='Alta',
            module='Plataformas',
            target=name,
            description=f"Nueva plataforma creada: {name}",
            status='success'
        )
        db.session.add(log)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Plataforma creada correctamente'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding platform: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@platforms_bp.route('/edit/<int:platform_id>', methods=['POST'])
@login_required
@admin_required
def edit_platform(platform_id):
    try:
        platform = Platform.query.get_or_404(platform_id)
        
        area_id = request.form.get('area_id')
        if not area_id or area_id == 'null' or area_id == 'undefined':
            return jsonify({'success': False, 'error': 'El Área es obligatoria. No puede dejar la plataforma sin un departamento vinculado.'}), 400
            
        platform.name = request.form.get('name')
        platform.description = request.form.get('description')
        platform.area_id = area_id
        platform.direct_link = request.form.get('direct_link')
        platform.icon = request.form.get('icon')
        platform.status = request.form.get('status')
        platform.bg_color = request.form.get('bg_color')
        platform.text_color = request.form.get('text_color')
        
        # Handle Logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                filename = f"plat_{platform.name.lower().replace(' ', '_')}_{file.filename}"
                upload_path = os.path.join(current_app.root_path, '../assets/img/platforms', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                file.save(upload_path)
                platform.logo_url = f"/assets/img/platforms/{filename}"

        # Handle Users
        user_ids = request.form.get('users')
        if user_ids:
            import json
            ids = json.loads(user_ids)
            users = User.query.filter(User.id.in_(ids)).all()
            platform.users = users

        # Audit Log
        log = AuditLog(
            user=current_user.email,
            action='Modificación',
            module='Plataformas',
            target=platform.name,
            description=f"Plataforma actualizada: {platform.name}",
            status='success'
        )
        db.session.add(log)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Plataforma actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing platform: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@platforms_bp.route('/delete/<int:platform_id>', methods=['GET'])
@login_required
@admin_required
def delete_platform(platform_id):
    try:
        platform = Platform.query.get_or_404(platform_id)
        platform_name = platform.name
        
        # ─── MANUAL CASCADE CLEANUP ───
        # 1. Remove all access requests for this platform
        from app.modules.core.models import AccessRequest
        AccessRequest.query.filter_by(platform_id=platform_id).delete()
        
        # 2. Clear user associations (pivot table)
        platform.users = []
        
        # 3. Delete the platform itself
        db.session.delete(platform)
        
        # Audit Log
        log = AuditLog(
            user=current_user.email,
            action='Baja',
            module='Plataformas',
            target=platform_name,
            description=f"Plataforma eliminada: {platform_name}",
            status='success'
        )
        db.session.add(log)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Plataforma eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting platform: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Endpoint aliases for legacy 1:1 JS compatibility
@platforms_bp.route('/add-platform', methods=['POST'])
@login_required
@admin_required
def add_platform_legacy():
    return add_platform()

@platforms_bp.route('/edit-platform/<int:platform_id>', methods=['POST'])
@login_required
@admin_required
def edit_platform_legacy(platform_id):
    return edit_platform(platform_id)

@platforms_bp.route('/delete-platform/<int:platform_id>', methods=['GET'])
@login_required
@admin_required
def delete_platform_legacy(platform_id):
    return delete_platform(platform_id)

@platforms_bp.route('/api/list/<int:area_id>')
@login_required
@admin_required
def get_platforms_by_area(area_id):
    platforms = Platform.query.filter_by(area_id=area_id).all()
    data = [{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'area_id': p.area_id,
        'direct_link': p.direct_link,
        'icon': p.icon,
        'status': p.status,
        'users_count': p.users.count() if hasattr(p, 'users') else 0,
        'bg_color': p.bg_color or '#6366f1',
        'text_color': getattr(p, 'text_color', '#ffffff'),
        'logo_url': p.logo_url,
        'user_ids': [u.id for u in p.users] if hasattr(p, 'users') else []
    } for p in platforms]
    return jsonify({'success': True, 'platforms': data})
