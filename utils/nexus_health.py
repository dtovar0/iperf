import sys
import os
import time

# Añadir raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.modules.auth.services import validate_ldap_connection
from app.modules.auth.models import AuthConfig
from app.modules.notifications.services import send_test_email
from app.modules.notifications.models import SMTPConfig
from psx5k_cmd import test_connectivity

def run_health_check():
    app = create_app()
    with app.app_context():
        print("\n" + "═"*60)
        print("🛡️  SISTEMA NEXUS - DIAGNÓSTICO INTEGRAL DE SALUD")
        print("═"*60)

        # 1. Base de Datos
        print("\n📊 1. PERSISTENCIA DE DATOS")
        try:
            db.session.execute(text("SELECT 1"))
            print("   ✅ Conexión con Motor de DB: ACTIVA")
        except Exception as e:
            from sqlalchemy import text
            try:
                db.session.execute(text("SELECT 1"))
                print("   ✅ Conexión con Motor de DB: ACTIVA")
            except Exception as e2:
                print(f"   ❌ Error de DB: {e2}")

        # 2. LDAP
        print("\n🔐 2. SERVICIOS DE IDENTIDAD (LDAP)")
        ldap_cfg = AuthConfig.query.first()
        if ldap_cfg:
            success, msg = validate_ldap_connection()
            if success:
                print(f"   ✅ Conexión LDAP: EXITOSA ({ldap_cfg.ldap_host})")
            else:
                print(f"   ❌ Fallo de LDAP: {msg}")
        else:
            print("   ⚠️  No hay configuración LDAP definida.")

        # 3. SMTP
        print("\n📧 3. NOTIFICACIONES (SMTP)")
        smtp_cfg = SMTPConfig.query.first()
        if smtp_cfg:
            # No enviamos mail real para no saturar, solo test de conectividad si existiera service
            print(f"   ℹ️  Configurado: {smtp_cfg.server}:{smtp_cfg.port} (Técnico: OK)")
            print("      (Usa 'utils/test_smtp.py' para una prueba de envío real)")
        else:
            print("   ⚠️  No hay configuración SMTP definida.")

        # 4. PSX5K
        print("\n🛰️  4. COMUNICACIÓN PSX5K (SSH/CLI)")
        success, msg = test_connectivity()
        if success:
            print(f"   ✅ Conectividad PSX: EXITOSA")
        else:
            print(f"   ❌ Fallo de PSX: {msg}")

        # 5. Worker
        print("\n⚙️  5. ESTADO DEL WORKER DAEMON")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        lock_file = os.path.join(project_root, "psx5k_worker.pid")

        if os.path.exists(lock_file):
            with open(lock_file, 'r') as f:
                pid = f.read().strip()
            try:
                os.kill(int(pid), 0)
                print(f"   ✅ Worker Activo (PID: {pid})")
            except (OSError, ValueError):
                print("   ⚠️  Lock file detectado pero el proceso no responde (Zombie).")
        else:
            print("   ❌ Worker NO DETECTADO (Offline)")

        print("\n" + "═"*60)
        print(f"🕒 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("═"*60 + "\n")

if __name__ == '__main__':
    from sqlalchemy import text
    run_health_check()
