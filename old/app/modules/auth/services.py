import ssl
import json
import os
import logging
from ldap3 import Server, Connection, ALL, Tls
from ldap3.utils.log import set_library_log_detail_level, EXTENDED
from datetime import datetime
from app.modules.notifications.services import send_notification_by_slug

if os.getenv('DEBUG_LDAP') == 'true':
    set_library_log_detail_level(EXTENDED)
    ldap3_logger = logging.getLogger('ldap3')
    ldap3_logger.setLevel(logging.DEBUG)
    if not ldap3_logger.handlers:
        os.makedirs(os.path.join(os.getcwd(), 'logs'), exist_ok=True)
        fh = logging.FileHandler(os.path.join(os.getcwd(), 'logs', 'ldap_debug.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        ldap3_logger.addHandler(fh)
        ldap3_logger.addHandler(logging.StreamHandler())

def authenticate_user_ldap(email, password):
    """
    Autentica un usuario contra LDAP y sincroniza su perfil local.
    """
    from app.modules.auth.models import AuthConfig, User
    from app import db

    config = AuthConfig.query.first()
    if not config or not config.ldap_host:
        return {"status": "error", "message": "LDAP no configurado"}

    try:
        # 1. Configurar Servidor
        tls_config = None
        if config.ldap_ssl:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        # Sanitizar host y puerto
        host = config.ldap_host.strip()
        port = int(config.ldap_port) if config.ldap_port else 389

        server = Server(
            host, 
            port=port, 
            use_ssl=config.ldap_ssl, 
            tls=tls_config,
            connect_timeout=5
        )

        # 2. Construir el User DN para el Bind
        # Algunos servidores requieren el DN completo, otros solo el CN/UID
        # 2. Construir filtro según el Atributo de Usuario configurado
        user_filter = f"({config.ldap_user_attr}={email})"
        
        # 3. Conexión de búsqueda
        with Connection(server, user=config.ldap_user, password=config.ldap_pass, auto_bind=True, auto_referrals=False) as conn:
            conn.search(config.ldap_base_dn, user_filter, attributes=['mail', 'displayName', 'cn', 'memberOf', 'sAMAccountName'])
            
            if not conn.entries:
                # ... (resto del código igual)
                # PROTOCOLO DE PURGA: Si el LDAP está arriba pero el usuario no existe, lo borramos localmente
                local_user = User.query.filter_by(email=email).first()
                if local_user:
                    from app.modules.audit.services import add_audit_log
                    db.session.delete(local_user)
                    db.session.commit()
                    add_audit_log("usuario borrado", status="warning", detail=f"Sincronía LDAP: Usuario {email} purgado por no existir en origen")
                    print(f"🗑️ Usuario {email} purgado localmente (Eliminado de LDAP).")
                
                return {"status": "error", "message": "Usuario no encontrado en el directorio corporativo"}
            
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # 4. Validar contraseña intentando un nuevo Bind con las credenciales del usuario
            try:
                conn_bind = Connection(server, user=user_dn, password=password, auto_bind=True)
                conn_bind.unbind()
            except Exception as bind_err:
                return {"status": "error", "message": "Contraseña LDAP incorrecta"}
                
            # Login Exitoso en LDAP -> Sincronizar Localmente
            try:
                # Mapeo: nombre -> displayName/cn, email -> mail
                nombre = str(user_entry.displayName.value) if 'displayName' in user_entry and user_entry.displayName else (str(user_entry.cn.value) if 'cn' in user_entry and user_entry.cn else email)
                ldap_email = str(user_entry.mail.value) if 'mail' in user_entry and user_entry.mail else email
                
                local_user = User.query.filter_by(email=ldap_email).first()
                is_new = False
                if not local_user:
                    local_user = User.query.filter_by(email=email).first()
                
                if not local_user:
                    is_new = True
                    local_user = User(
                        email=ldap_email,
                        nombre=nombre,
                        role='usuario',
                        auth_source='ldap',
                        is_active=True
                    )
                    # Clave local deshabilitada
                    local_user.password_hash = None
                    db.session.add(local_user)
                    from app.modules.audit.services import add_audit_log
                    add_audit_log("usuario creado", status="success", detail=f"Sincronía LDAP: Shadow user '{ldap_email}' generado (Origen: mail)")
                else:
                    local_user.email = ldap_email
                    local_user.nombre = nombre
                    local_user.auth_source = 'ldap'
                
                # Actualizar telemetría de sesión
                local_user.last_login_at = datetime.now()
                
                # Lógica de Mapeo de Roles Avanzado (JSON + Legacy Fallback)
                new_role = 'usuario' # Default
                member_of = [str(g).lower() for g in user_entry.memberOf] if 'memberOf' in user_entry else []

                # 1. Intentar Mapeo Dinámico (JSON)
                if config.ldap_role_mappings:
                    import json
                    try:
                        mappings = json.loads(config.ldap_role_mappings)
                        for mapping in mappings:
                            m_group = mapping.get('group', '').strip().lower()
                            m_role = mapping.get('role', 'usuario')
                            if any(m_group in group for group in member_of):
                                new_role = m_role
                                break
                    except Exception as e:
                        print(f"Error parsing role mappings: {e}")

                # 2. Fallback a Legacy
                if new_role == 'usuario' and config.ldap_group_admin:
                    legacy_groups = [g.strip().lower() for g in config.ldap_group_admin.split(',')]
                    if any(any(lg in group for lg in legacy_groups) for group in member_of):
                        new_role = 'administrador'
                
                local_user.role = new_role
                
                db.session.commit()
                
                # REASEGURO CONTRA 'None' EN FLASK-LOGIN
                if not local_user.id:
                    # En caso extremo de que un rollback lo haya desadjuntado temporalmente
                    db.session.add(local_user)
                    db.session.commit()
                    db.session.refresh(local_user)

                # Notificar bienvenida LDAP (Solo si es nuevo y habilitado)
                if is_new and os.getenv('NOTIFY_USER_CREATED', 'true').lower() == 'true':
                    base_url = os.getenv('BASE_URL', 'http://10.224.2.146')
                    send_notification_by_slug('usuario_creado', ldap_email, context={
                        'nombre': nombre,
                        'usuario': ldap_email,
                        'base_url': base_url,
                        'url': f"{base_url}/auth/login"
                    })

                return {"status": "success", "user": local_user}

            except Exception as sync_err:
                db.session.rollback()
                print(f"ERROR LDAP DB SYNC: {sync_err}")
                from flask import current_app
                current_app.logger.error(f"ERROR LDAP DB SYNC: {sync_err}")
                return {"status": "error", "message": f"Fallo al registrar/actualizar usuario en base de datos: {str(sync_err)}"}

    except Exception as e:
        return {"status": "error", "message": f"Error LDAP: {str(e)}"}

def purge_inactive_users(days=30):
    """
    RUTINA DE HIGIENE: Elimina usuarios que no han iniciado sesión en X días.
    """
    from app.modules.auth.models import User
    from app.modules.audit.services import add_audit_log
    from app import db
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)
    
    try:
        # No purgar administradores nunca por seguridad
        inactive_users = User.query.filter(
            User.last_login_at < cutoff,
            User.role != 'administrador'
        ).all()
        
        count = len(inactive_users)
        purged_names = [user.email for user in inactive_users]
        
        for user in inactive_users:
            email = user.email
            db.session.delete(user)
            add_audit_log("usuario purgado", status="warning", detail=f"Inactividad > {days} días: Usuario {email} eliminado automáticamente")
            
        db.session.commit()
        return {"status": "success", "purged_count": count, "purged_names": purged_names}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": "Error al conectar con LDAP."}

def validate_ldap_connection(host, port, use_ssl=False, bind_dn=None, bind_pass=None):
    """
    Realiza una prueba de conexión y bind contra un servidor LDAP.
    """
    try:
        tls_config = None
        if use_ssl:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        server = Server(
            host, 
            port=int(port), 
            use_ssl=use_ssl, 
            tls=tls_config, 
            get_info=ALL,
            connect_timeout=5
        )

        with Connection(server, user=bind_dn, password=bind_pass, auto_bind=True, auto_referrals=False) as conn:
            return {
                "status": "success",
                "message": "Conexión establecida correctamente",
                "info": str(server.info) if server.info else "Anonimo"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Fallo de conexión: {str(e)}"
        }
