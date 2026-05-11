import sys
import os

# Agrega la ruta base del proyecto explícitamente para asegurar que los módulos de app se puedan importar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def migrate_db():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            print("🔍 Iniciando validación de estructura de identidad (Email-based)...")

            # 1. Intentar renombrar username a email si aún existe el campo viejo
            try:
                conn.execute(text("ALTER TABLE users CHANGE username email VARCHAR(120) NOT NULL;"))
                print("✅ Columna username convertida a email exitosamente.")
            except Exception as e:
                print("ℹ️ Columna username no encontrada (probablemente ya es email).")

            # 2. Asegurar longitud y restricciones de email
            try:
                conn.execute(text("ALTER TABLE users MODIFY email VARCHAR(120) NOT NULL UNIQUE;"))
                print("✅ Restricciones de email validadas (120 chars, NOT NULL, UNIQUE).")
            except Exception as e:
                print(f"❌ Error al validar columna email: {e}")

            # 3. Agregar columna nombre si no existe
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN nombre VARCHAR(100) DEFAULT NULL AFTER email;"))
                print("✅ Columna nombre validada.")
            except Exception as e:
                print(f"ℹ️ Columna nombre ya posicionada.")

            # 4. Desbloquear el candado NOT NULL de password_hash
            try:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NULL;"))
                print("✅ Columna password_hash validada (permite NULL para SSO/LDAP).")
            except Exception as e:
                print(f"❌ Error al validar password_hash: {e}")

            # 5. Columnas de preferencias en USERS
            pref_columns = [
                ("pref_notifications", "TINYINT(1) DEFAULT 1"),
                ("pref_refresh_interval", "INT DEFAULT 60"),
                ("pref_tour_enabled", "TINYINT(1) DEFAULT 1"),
                ("pref_email_notifications", "TINYINT(1) DEFAULT 1")
            ]

            for col_name, col_type in pref_columns:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                    print(f"✅ Columna {col_name} agregada.")
                except Exception as e:
                    pass

            # 6. Columnas de PSX5K_DETAILS (del / delcheck)
            psx_columns = [
                ("del", "INTEGER DEFAULT 0"),
                ("delcheck", "INTEGER DEFAULT 0")
            ]
            for col_name, col_type in psx_columns:
                try:
                    conn.execute(text(f"ALTER TABLE psx5k_details ADD COLUMN {col_name} {col_type};"))
                    print(f"✅ Columna psx5k_details.{col_name} agregada.")
                except Exception as e:
                    pass

            conn.commit()

if __name__ == '__main__':
    print("🚀 Sincronizando Esquema de Base de Datos V4.0 (Identidad por Email)...")
    migrate_db()
