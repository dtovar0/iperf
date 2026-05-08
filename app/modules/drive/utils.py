import os
import secrets
from cryptography.fernet import Fernet
from app import db
from app.modules.core.models import DriveActivity, Area, Platform
from app.modules.auth.models import User
from app.modules.audit.models import AuditLog

class SecretManager:
    _key_file = 'secret.key'
    _key = None

    @classmethod
    def get_key(cls):
        # Prioritize Environment Variable for Production Security
        env_key = os.environ.get('MASTER_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()

        if not cls._key:
            if os.path.exists(cls._key_file):
                with open(cls._key_file, 'rb') as f:
                    cls._key = f.read()
            else:
                cls._key = Fernet.generate_key()
                with open(cls._key_file, 'wb') as f:
                    f.write(cls._key)
        return cls._key

    @classmethod
    def encrypt(cls, value):
        if not value: return None
        f = Fernet(cls.get_key())
        return f.encrypt(value.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_value):
        if not encrypted_value: return None
        f = Fernet(cls.get_key())
        return f.decrypt(encrypted_value.encode()).decode()

class StorageManager:
    # Definir storage relativo a la raíz del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ROOT_STORAGE = os.path.normpath(os.path.join(BASE_DIR, 'storage'))
    
    FORBIDDEN_EXTENSIONS = {
        '.exe', '.msi', '.bat', '.sh', '.php', '.phtml', '.php5', '.js', '.jsx',
        '.py', '.pyc', '.pl', '.cgi', '.asp', '.aspx', '.jsp', '.jspx', '.rb',
        '.vbs', '.com', '.scr', '.pif', '.hta', '.cpl'
    }

    @classmethod
    def sanitize_filename(cls, filename):
        import re
        from werkzeug.utils import secure_filename
        filename = "".join(ch for ch in filename if ord(ch) > 31)
        name = secure_filename(filename)
        parts = name.split('.')
        if len(parts) > 2:
            name = "_".join(parts[:-1]) + "." + parts[-1]
        return name

    @classmethod
    def is_safe_file(cls, filename):
        ext = os.path.splitext(filename.lower())[1]
        if ext in cls.FORBIDDEN_EXTENSIONS:
            return False
        if not ext:
            return False
        return True

    @classmethod
    def get_safe_path(cls, requested_path):
        if not requested_path:
            return cls.ROOT_STORAGE
            
        if not os.path.exists(cls.ROOT_STORAGE):
            os.makedirs(cls.ROOT_STORAGE)

        clean_req = requested_path.replace('..', '').replace('\\', '/')
        # Si la ruta ya es absoluta y está dentro de ROOT_STORAGE, la usamos
        if os.path.isabs(clean_req) and clean_req.startswith(cls.ROOT_STORAGE):
            abs_requested = os.path.normpath(clean_req)
        else:
            # Si no, la unimos a ROOT_STORAGE
            abs_requested = os.path.normpath(os.path.join(cls.ROOT_STORAGE, clean_req.lstrip('/')))

        common = os.path.commonpath([cls.ROOT_STORAGE, abs_requested])
        if common != cls.ROOT_STORAGE:
            raise PermissionError("Acceso a ubicación no autorizada.")

        return abs_requested

def log_drive_activity(file_name, file_path, action, user_id=None, file_size=0, area_id=None, platform_id=None):
    from flask import request
    ip = request.remote_addr if request else None
    ua = request.user_agent.string if request and request.user_agent else None

    new_log = DriveActivity(
        file_name=file_name,
        file_path=file_path,
        action=action,
        user_id=user_id,
        file_size=file_size,
        area_id=area_id,
        platform_id=platform_id,
        ip_address=ip,
        user_agent=ua
    )
    db.session.add(new_log)
    db.session.commit()
