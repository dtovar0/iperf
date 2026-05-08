import sys
import os
import getpass

# Añadir el raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.modules.auth.models import User
from sqlalchemy import text

def clean_database():
    app = create_app()
    with app.app_context():
        print("⚠️  ADVERTENCIA: Esto eliminará toda la información operativa y usuarios.")
        print("Las configuraciones del sistema se mantendrán intactas.")
        
        confirm = input("¿Estás seguro de continuar? (escribe 'si' para confirmar): ")
        if confirm.lower() != 'si':
            print("Operación cancelada.")
            return

        print("\nConfigurando usuario administrador maestro...")
        admin_pass = getpass.getpass("🔑 Ingresa la nueva contraseña para el usuario 'admin': ")
        confirm_pass = getpass.getpass("🔑 Confirma la contraseña: ")
        
        if admin_pass != confirm_pass:
            print("❌ Las contraseñas no coinciden. Abortando.")
            return
            
        if len(admin_pass) < 6:
            print("❌ La contraseña es demasiado corta. Abortando.")
            return

        print("\n🧹 Limpiando base de datos...")
        try:
            # Deshabilitar verificación de Foreign Keys temporalmente para MySQL/SQLite
            if engine_is_mysql():
                db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            else:
                db.session.execute(text("PRAGMA foreign_keys = OFF;"))

            # Tablas operativas a purgar
            tables_to_clean = [
                'platform_access_requests',
                'user_platform_favorites',
                'platforms',
                'areas',
                'psx5k_command_logs',
                'psx5k_history',
                'psx5k_details',
                'psx5k_tasks',
                'psx5k_jobs',
                'audit_logs',
                'in_app_notifications',
                'users'
            ]

            for table in tables_to_clean:
                # Comprobar si existe primero usando el inspector
                if db.engine.dialect.has_table(db.engine.connect(), table):
                    db.session.execute(text(f"DELETE FROM {table};"))
                    print(f"  - Tabla {table} purgada.")

            db.session.commit()

            print("\n👤 Restaurando usuario 'admin'...")
            admin_user = User(
                email='admin',
                nombre='Administrador',
                role='administrador',  
                auth_source='local',
                is_active=True
            )
            admin_user.set_password(admin_pass)
            db.session.add(admin_user)
            db.session.commit()
            print("  ✅ Usuario 'admin' recreado exitosamente.")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error durante la limpieza: {str(e)}")
        finally:
            # Rehabilitar Foreign Keys
            try:
                if engine_is_mysql():
                    db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                else:
                    db.session.execute(text("PRAGMA foreign_keys = ON;"))
                db.session.commit()
            except:
                pass
                
        print("\n✨ Limpieza de base de datos finalizada exitosamente.")

def engine_is_mysql():
    return 'mysql' in db.engine.dialect.name.lower()

if __name__ == '__main__':
    clean_database()
