import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.modules.auth.models import User, AuthConfig
from app.modules.auth.services import validate_ldap_connection
from app.modules.audit.services import add_audit_log
from app.modules.notifications.services import send_notification_by_slug

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    try:
        # 1. Si ya está logueado, ir al inicio
        if current_user.is_authenticated:
            return redirect(url_for('core.index'))
            
        # --- DEBUG DE CABECERAS (SI ESTÁ HABILITADO) ---
        if os.getenv('DEBUG_AUTH', 'false').lower() == 'true':
            print("\n" + "="*50)
            print("DEBUG AUTH: REVISANDO CABECERAS ENTRANTES")
            for header, value in request.headers.items():
                print(f"  {header}: {value}")
            print("="*50 + "\n")

        # 2. INTENTO DE SSO / AUTHELIA (Soporta GET y POST)
        if os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true':
            header_user = os.getenv('AUTHELIA_HEADER_USER', 'Remote-Email')
            authelia_user = request.headers.get(header_user)
            
            if authelia_user:
                print(f"DEBUG: Usuario detectado -> {authelia_user}")
                header_name = os.getenv('AUTHELIA_HEADER_NAME', 'Remote-Name')
                header_groups = os.getenv('AUTHELIA_HEADER_GROUPS', 'Remote-Groups')
                
                print("DEBUG: Buscando usuario en DB...")
                user = User.query.filter_by(email=authelia_user).first()
                authelia_name = request.headers.get(header_name, authelia_user)
                authelia_groups = request.headers.get(header_groups, '')
                
                # Lógica de Roles Dinámica (Soporta múltiples grupos de admin)
                inferred_role = 'usuario'
                admin_groups_env = os.getenv('AUTHELIA_GROUP_ADMIN', 'administrador')
                admin_groups = [g.strip().lower() for g in admin_groups_env.split(',')]
                
                if authelia_groups:
                    user_groups = [g.strip().lower() for g in authelia_groups.split(',')]
                    # Si el usuario pertenece a CUALQUIERA de los grupos de admin definidos
                    if any(group in user_groups for group in admin_groups):
                        inferred_role = 'administrador'

                if not user:
                    print("DEBUG: Usuario nuevo. Creando registro...")
                    user = User(
                        email=authelia_user,
                        nombre=authelia_name,
                        role=inferred_role,
                        auth_source='sso'
                    )
                    db.session.add(user)
                    db.session.commit()
                    # Notificar bienvenida SSO
                    if os.getenv('NOTIFY_USER_CREATED', 'true').lower() == 'true':
                        base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
                        send_notification_by_slug('usuario_creado', authelia_user, context={
                            'nombre': authelia_name,
                            'usuario': authelia_user,
                            'base_url': base_url,
                            'url': f"{base_url}/auth/login"
                        })
                else:
                    print("DEBUG: Usuario existente. Actualizando metadatos...")
                    user.nombre = authelia_name
                    user.role = inferred_role
                    db.session.commit()
                
                print(f"DEBUG: Procediendo a login_user para {user.email}")
                login_user(user, remember=True)
                print("DEBUG: Registro en auditoría...")
                add_audit_log(f"ACCESO SSO: {authelia_user}", status="success", detail=f"Sesión iniciada exitosamente vía Portal Authelia")
                print("DEBUG: Redirigiendo a index...")
                return redirect(url_for('core.index'))

        # 3. LOGIN TRADICIONAL (Solo si es POST)
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            auth_type = request.form.get("auth_type", "directory")
            
            if auth_type == "directory":
                from app.modules.auth.services import authenticate_user_ldap
                ldap_result = authenticate_user_ldap(email, password)
                if ldap_result.get("status") == "success":
                    user = ldap_result["user"]
                    login_user(user, remember=True)
                    add_audit_log(f"ACCESO DIRECTORIO: {email}", status="success", detail=f"Autenticación corporativa exitosa")
                    return redirect(url_for('core.index'))
                else:
                    flash(f"Error: {ldap_result.get('message')}", "error")
            else:
                user = User.query.filter_by(email=email).first()
                if user and user.check_password(password):
                    login_user(user, remember=True)
                    add_audit_log(f"ACCESO LOCAL: {email}", status="success", detail=f"Autenticación manual exitosa")
                    return redirect(url_for('core.index'))
                flash("Credenciales incorrectas", "error")

        # 4. FALLBACK: Mostrar formulario de login manual
        return render_template("login.html", sso_enabled=os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true')

    except Exception as e:
        import traceback
        print("\n" + "!"*50)
        print(f"ERROR CRÍTICO EN LOGIN: {str(e)}")
        traceback.print_exc()
        print("!"*50 + "\n")
        from flask import current_app
        current_app.logger.error(f"Error en login: {e}")
        return render_template("login.html", error="Error en el servicio de autenticación")

@auth_bp.route("/users/purge", methods=["POST"])
@login_required
def purge_users():
    """
    Ruta administrativa para ejecutar la limpieza de inactividad.
    """
    if current_user.role != 'administrador':
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
        
    try:
        from app.modules.auth.services import purge_inactive_users
        result = purge_inactive_users(days=30)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": "Ocurrió un error al procesar el usuario."}), 500

@auth_bp.route("/logout")
@login_required
def logout():
    user_email = current_user.email
    logout_user()
    add_audit_log(f"CIERRE DE SESIÓN: {user_email}", status="success", detail=f"El usuario ha finalizado su sesión de forma manual")
    
    # --- LOGOUT COORDINADO CON AUTHELIA (SSO) ---
    if os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true':
        slo_url = os.getenv('AUTHELIA_SLO_URL')
        if slo_url:
            # Redirigimos al login para romper el bucle
            redirect_url = f"{slo_url}?rd={request.host_url}auth/login"
            return redirect(redirect_url)
        
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route("/")
@login_required
def index():
    try:
        config = AuthConfig.query.first()
        sso_enabled = os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true'
        return render_template("auth.html", config=config, sso_enabled=sso_enabled)
    except Exception as e:
        current_app.logger.error(f"Error en auth.index: {e}")
        return render_template("auth.html", config=None)

@auth_bp.route("/save", methods=["POST"])
def save():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        config = AuthConfig.query.first()
        if not config:
            config = AuthConfig()
            db.session.add(config)
            
        # Update Auth Config
        if "ldap_host" in data: config.ldap_host = data["ldap_host"]
        if "ldap_port" in data: config.ldap_port = data["ldap_port"]
        if "ldap_ssl" in data: config.ldap_ssl = data["ldap_ssl"]
        if "ldap_base_dn" in data: config.ldap_base_dn = data["ldap_base_dn"]
        if "ldap_user" in data: config.ldap_user = data["ldap_user"]
        if "ldap_pass" in data: config.ldap_pass = data["ldap_pass"]
        if "ldap_user_attr" in data: config.ldap_user_attr = data["ldap_user_attr"]
        if "ldap_group_admin" in data: config.ldap_group_admin = data["ldap_group_admin"]
        if "ldap_group_user" in data: config.ldap_group_user = data["ldap_group_user"]
        if "ldap_role_mappings" in data: config.ldap_role_mappings = data["ldap_role_mappings"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuración de Directorio Guardada"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error al actualizar credenciales."}), 500

@auth_bp.route("/users/list")
@login_required
def list_users():
    search = request.args.get('search', '').lower()
    
    query = User.query
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) | 
            (User.nombre.ilike(f'%{search}%')) | 
            (User.role.ilike(f'%{search}%')) |
            (User.auth_source.ilike(f'%{search}%'))
        )
    
    users = query.all()
    user_list = []
    for u in users:
        # Map db state to UI status
        status = 'active' if u.is_active else 'inactive'
        
        user_list.append({
            "id": u.id,
            "email": u.email,
            "username": u.email, # Keep temporarily for JS compatibility during transition if needed, or just remove
            "nombre": u.nombre,
            "role": u.role,
            "source": u.auth_source or 'local',
            "status": status
        })
        
    return jsonify(user_list)

@auth_bp.route("/users/create", methods=["POST"])
@login_required
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Faltan datos"}), 400
            
        # Validar si ya existe
        target_email = data.get('email')
        if not target_email:
            return jsonify({"status": "error", "message": "Email es requerido"}), 400

        if User.query.filter_by(email=target_email).first():
            return jsonify({"status": "error", "message": "Este email ya está registrado"}), 400
            
        new_user = User(
            email=target_email,
            nombre=data.get('nombre', ''),
            role=data['role'],
            is_active=True
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        # Notificar bienvenida Manual
        if os.getenv('NOTIFY_USER_CREATED', 'true').lower() == 'true':
            base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
            send_notification_by_slug('usuario_creado', target_email, context={
                'nombre': data.get('nombre', ''),
                'usuario': target_email,
                'base_url': base_url,
                'url': f"{base_url}/auth/login"
            })

        add_audit_log("usuario creado", status="success", detail=f"Se creó el usuario: {target_email}")
        
        return jsonify({"status": "success", "message": "Usuario creado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error del sistema en el entorno LDAP."}), 500

@auth_bp.route("/users/delete", methods=["POST"])
@login_required
def delete_users():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({"status": "error", "message": "No se proporcionaron IDs"}), 400
            
        User.query.filter(User.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({"status": "success", "message": f"{len(ids)} usuarios eliminados"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "La conexión LDAP ha fallado temporalmente."}), 500

@auth_bp.route("/users/update", methods=["POST"])
@login_required
def update_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user = User.query.get(user_id)
        if not user:
             return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

        target_email = data.get('email', '').strip()
        nombre = data.get('nombre', '').strip()

        # Safeguard: Prevent hijacking 'admin' identifier
        is_reserved = target_email.lower() == 'admin' or nombre.lower() == 'admin'
        is_already_admin = (user.email.lower() == 'admin' or user.nombre.lower() == 'admin')
        
        if is_reserved and not is_already_admin:
            return jsonify({"status": "error", "message": "El identificador 'admin' es reservado del sistema."}), 403

        if target_email and target_email != user.email: 
            user.email = target_email
            
        if nombre and nombre != user.nombre: 
            user.nombre = nombre
            
        role = data.get('role', '').strip()
        if role and role != user.role: 
            user.role = role
        
        password = data.get('password', '').strip()
        if password:
            user.set_password(password)
            
        db.session.commit()

        # REFRESH SESSION: If I am editing myself, I must re-login to avoid being kicked out
        if current_user.is_authenticated and user.id == current_user.id:
            login_user(user, remember=True)

        return jsonify({"status": "success", "message": "Usuario actualizado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Autenticación LDAP falló en el controlador."}), 500

@auth_bp.route("/test_ldap", methods=["POST"])
@login_required
def test_ldap():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
            
        result = validate_ldap_connection(
            host=data.get("ldap_host"),
            port=data.get("ldap_port"),
            use_ssl=data.get("ldap_ssl", False),
            bind_dn=data.get("ldap_user"),
            bind_pass=data.get("ldap_pass")
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Fallo en la sincronización de roles LDAP."}), 500

@auth_bp.route("/preferences/save", methods=["POST"])
@login_required
def save_preferences():
    """
    Guarda las preferencias de interfaz del usuario actual.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
            
        if "notifications" in data: current_user.pref_notifications = data["notifications"]
        if "email_notifications" in data: current_user.pref_email_notifications = data["email_notifications"]
        if "refresh_interval" in data: current_user.pref_refresh_interval = data["refresh_interval"]
        if "tour_enabled" in data: current_user.pref_tour_enabled = data["tour_enabled"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Preferencias del sistema actualizadas"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error al guardar preferencias"}), 500
