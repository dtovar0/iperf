from flask import Blueprint, render_template, request, jsonify, g
from flask_login import login_required, current_user, login_user
from app.decorators import admin_required
from app import db
from app.modules.auth.models import User, AuthConfig
from app.modules.audit.models import AuditLog
from app.modules.audit.services import add_audit_log
import json
from datetime import datetime
import ssl
from ldap3 import Server, Connection, ALL, Tls

users_bp = Blueprint('users_module', __name__, url_prefix='/admin')

@users_bp.route('/users')
@login_required
@admin_required
def users_list():
    users = User.query.all()
    
    users_data = []
    for u in users:
        users_data.append({
            'id': u.id,
            'name': u.nombre or u.email,
            'email': u.email,
            'role': u.role,
            'status': 'Activo' if u.is_active else 'Inactivo',
            'source': u.auth_source or 'local'
        })
        
    return render_template('users.html', users_json=users_data)

@users_bp.route('/add-user', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        nombre = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role', 'usuario')
        password = request.form.get('password', 'nexus123') 
        status_str = request.form.get('status', 'Activo')
        auth_source = request.form.get('auth_source', 'local')
        
        if email.lower().strip() == 'admin' or nombre.lower().strip() == 'admin':
            return jsonify({"success": False, "error": "El identificador 'admin' es reservado del sistema."}), 403

        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "error": "El correo ya está registrado."}), 409

        new_user = User(
            nombre=nombre,
            email=email,
            role=role,
            is_active=(status_str == 'Activo'),
            auth_source=auth_source
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        add_audit_log(f"CREAR USUARIO: {email}", status="success", detail=f"Usuario {nombre} creado manualmente")
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@users_bp.route('/edit-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
            
        role = request.form.get('role', '').strip()
        status_str = request.form.get('status', '').strip()
        
        if role and role != user.role: 
            user.role = role
        
        if status_str: 
            new_active = (status_str == 'Activo')
            if new_active != user.is_active:
                user.is_active = new_active
        
        # Update Password ONLY if a real value is provided
        new_password = request.form.get('password', '').strip()
        if new_password and user.auth_source == 'local':
            user.set_password(new_password)
            add_audit_log(f"CAMBIO PASSWORD: {user.email}", status="warning", detail=f"Contraseña actualizada para {user.email}")

        db.session.commit()
        
        # REFRESH SESSION if self-editing
        if current_user.is_authenticated and user.id == current_user.id:
            login_user(user, remember=True)

        add_audit_log(f"MODIFICAR USUARIO: {user.email}", status="success", detail=f"Perfil de usuario actualizado")
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@users_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
            
        if user.id == current_user.id:
            return jsonify({"success": False, "error": "No puedes eliminar tu propia cuenta"}), 400
            
        email = user.email
        db.session.delete(user)
        db.session.commit()
        
        add_audit_log(f"ELIMINAR USUARIO: {email}", status="warning", detail=f"Usuario eliminado del sistema")
        
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@users_bp.route('/ldap-search-api')
@login_required
@admin_required
def ldap_search_api():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"success": False, "error": "Faltan criterios de búsqueda"}), 400
        
    config = AuthConfig.query.first()
    if not config or not config.ldap_host:
        return jsonify({"success": False, "error": "LDAP no configurated"}), 400
        
    try:
        tls_config = None
        if config.ldap_ssl:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        server = Server(
            config.ldap_host, 
            port=int(config.ldap_port), 
            use_ssl=config.ldap_ssl, 
            tls=tls_config,
            connect_timeout=5
        )

        user_filter = f"(|(sAMAccountName=*{query}*)(mail=*{query}*)(displayName=*{query}*))"
        
        with Connection(server, user=config.ldap_user, password=config.ldap_pass, auto_bind=True, auto_referrals=False) as conn:
            conn.search(config.ldap_base_dn, user_filter, attributes=['mail', 'displayName', 'cn', 'sAMAccountName', 'uid'])
            
            users = []
            for entry in conn.entries:
                users.append({
                    "displayName": str(entry.displayName.value) if 'displayName' in entry else (str(entry.cn.value) if 'cn' in entry else ''),
                    "mail": str(entry.mail.value) if 'mail' in entry else '',
                    "sAMAccountName": str(entry.sAMAccountName.value) if 'sAMAccountName' in entry else (str(entry.uid.value) if 'uid' in entry else ''),
                    "cn": str(entry.cn.value) if 'cn' in entry else ''
                })
                
            return jsonify({"success": True, "users": users})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
