from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app.decorators import admin_required
from app import db
from app.modules.settings.models import SystemConfig
from app.modules.auth.models import User, AuthConfig
from app.modules.notifications.models import SMTPConfig, NotificationTemplate
from app.modules.audit.models import AuditLog
import json
import zipfile
import io
from datetime import datetime

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

@settings_bp.route("/")
@login_required
@admin_required
def index():
    config = SystemConfig.query.first()
    return render_template("settings.html", sys_config=config)

@settings_bp.route("/export", methods=["GET"])
@login_required
@admin_required
def export_config():
    try:
        # 1. Gather all system data
        data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "export_by": current_user.email,
            "payload": {
                "system_config": SystemConfig.query.first().to_dict() if SystemConfig.query.first() else {},
                "auth_config": AuthConfig.query.first().to_dict() if AuthConfig.query.first() else {},
                "smtp_config": SMTPConfig.query.first().to_dict() if SMTPConfig.query.first() else {},
                "users": [
                    {
                        "email": u.email,
                        "nombre": u.nombre,
                        "password_hash": u.password_hash,
                        "role": u.role,
                        "auth_source": u.auth_source,
                        "is_active": u.is_active
                    } for u in User.query.filter_by(auth_source='local').all()
                ],
                "templates": [t.to_dict() for t in NotificationTemplate.query.all()]
            }
        }

        # 2. Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr("nexus_config.json", json.dumps(data, indent=4))
            
        zip_buffer.seek(0)
        
        # Audit Log
        audit = AuditLog(
            user=current_user.email,
            action="EXPORT_CONFIG_ZIP",
            ip_address=request.remote_addr,
            status="success",
            detail="Portal empaquetado en ZIP profesional"
        )
        db.session.add(audit)
        db.session.commit()

        date_str = datetime.now().strftime("%Y-%m-%d")
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"nexus_backup_{date_str}.zip"
        )
    except Exception as e:
        return jsonify({"status": "error", "message": "Ocurrió un error al guardar la configuración del sistema."}), 500

@settings_bp.route("/import", methods=["POST"])
@login_required
@admin_required
def import_config():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No se recibió el archivo"}), 400
        
        file = request.files['file']
        
        if not zipfile.is_zipfile(file):
            return jsonify({"status": "error", "message": "El archivo cargado no es un paquete ZIP válido"}), 400
            
        file.seek(0)
        with zipfile.ZipFile(file, "r") as zip_ref:
            if "nexus_config.json" not in zip_ref.namelist():
                return jsonify({"status": "error", "message": "Estructura corrupta: nexus_config.json no encontrado en el ZIP"}), 400
            
            with zip_ref.open("nexus_config.json") as json_file:
                import_data = json.load(json_file)
        
        payload = import_data.get("payload", {})

        # 1. Restore System Config
        sys_data = payload.get("system_config")
        if sys_data:
            config = SystemConfig.query.first() or SystemConfig()
            config.portal_name = sys_data.get("portal_name", config.portal_name)
            config.portal_identity_type = sys_data.get("portal_identity_type", config.portal_identity_type)
            config.portal_icon = sys_data.get("portal_icon", config.portal_icon)
            config.bg_color = sys_data.get("bg_color", config.bg_color)
            config.text_color = sys_data.get("text_color", config.text_color)
            db.session.add(config)

        # 2. Restore Auth Config (LDAP)
        auth_data = payload.get("auth_config")
        if auth_data:
            aconfig = AuthConfig.query.first() or AuthConfig()
            for key, val in auth_data.items():
                if hasattr(aconfig, key): setattr(aconfig, key, val)
            db.session.add(aconfig)

        # 3. Restore SMTP Config
        smtp_data = payload.get("smtp_config")
        if smtp_data:
            sconfig = SMTPConfig.query.first() or SMTPConfig()
            for key, val in smtp_data.items():
                if hasattr(sconfig, key): setattr(sconfig, key, val)
            db.session.add(sconfig)

        # 4. Restore Templates (Clear and rewrite to avoid slugs conflict)
        templates_data = payload.get("templates", [])
        if templates_data:
            NotificationTemplate.query.delete()
            for t_data in templates_data:
                template = NotificationTemplate(
                    slug=t_data.get("slug"),
                    name=t_data.get("name"),
                    subject=t_data.get("subject"),
                    body=t_data.get("body"),
                    is_html=t_data.get("is_html", False)
                )
                db.session.add(template)

        # 5. Restore Local Users (Only if not exist to prevent collision with current admin)
        users_data = payload.get("users", [])
        for u_data in users_data:
            exists = User.query.filter_by(email=u_data.get('email')).first()
            if not exists:
                user = User(
                    email=u_data.get('email'),
                    nombre=u_data.get('nombre'),
                    password_hash=u_data.get('password_hash'),
                    role=u_data.get('role', 'usuario'),
                    auth_source='local',
                    is_active=u_data.get('is_active', True)
                )
                db.session.add(user)

        # Audit Log
        audit = AuditLog(
            user=current_user.email,
            action="IMPORT_CONFIG",
            ip_address=request.remote_addr,
            status="success",
            detail=f"Restauración completa realizada por: {import_data.get('export_by', 'desconocido')}"
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({"status": "success", "message": "Sistema restaurado correctamente. Reinicia para aplicar todos los cambios."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error en importación: {str(e)}"}), 500

@settings_bp.route("/save", methods=["POST"])
@login_required
@admin_required
def save():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        config = SystemConfig.query.first()
        if not config:
            config = SystemConfig()
            db.session.add(config)
            
        # Update General Config
        if "portal_name" in data: config.portal_name = data["portal_name"]
        
        # Identity Logic (Icon vs Image)
        identity_type = data.get("portal_identity_type", "icon")
        config.portal_identity_type = identity_type
        
        raw_identity = data.get("portal_icon", "")
        
        if identity_type == "image" and raw_identity.startswith("data:image"):
            # PHYSICAL SAVING LOGIC
            import base64
            import os
            
            # 1. Define Paths
            branding_dir = os.path.join(os.getcwd(), 'assets', 'img', 'branding')
            if not os.path.exists(branding_dir):
                os.makedirs(branding_dir)
                
            # 2. Extract Base64 Data
            try:
                header, encoded = raw_identity.split(",", 1)
                file_ext = header.split("/")[1].split(";")[0] # png, jpeg, etc
                filename = f"portal_logo.{file_ext}"
                filepath = os.path.join(branding_dir, filename)
                
                # 3. Write File
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(encoded))
                    
                # 4. Store Relative Path in DB
                config.portal_icon = f"/assets/img/branding/{filename}"
            except Exception as e:
                print(f"Error saving physical file: {e}")
                config.portal_icon = raw_identity # Fallback to base64 if fails
        else:
            # For Icons, store the SVG/string as is
            config.portal_icon = raw_identity
            
        if "bg_color" in data: config.bg_color = data["bg_color"]
        if "text_color" in data: config.text_color = data["text_color"]
        
        # Banner Logic
        if "portal_banner" in data and data["portal_banner"].startswith("data:image"):
            import base64
            import os
            branding_dir = os.path.join(os.getcwd(), 'assets', 'img', 'branding')
            if not os.path.exists(branding_dir): os.makedirs(branding_dir)
            
            try:
                header, encoded = data["portal_banner"].split(",", 1)
                file_ext = header.split("/")[1].split(";")[0]
                filename = f"portal_banner.{file_ext}"
                filepath = os.path.join(branding_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(encoded))
                config.portal_banner = f"/assets/img/branding/{filename}"
            except Exception as e:
                print(f"Error saving banner: {e}")
                config.portal_banner = data["portal_banner"]
        elif "portal_banner" in data:
            config.portal_banner = data["portal_banner"]
        
        # Add Audit Log Entry
        audit = AuditLog(
            user=current_user.email,
            action="SET_IDENTITY",
            ip_address=request.remote_addr,
            status="success",
            detail=f"Identidad actualizada ({identity_type}): {config.portal_name}"
        )
        db.session.add(audit)
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Ajustes e Historial Sincronizados"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Fallo interno al realizar la purga programada."}), 500
