import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

def sync_schema():
    with app.app_context():
        print("🔍 Comprobando integridad del esquema de base de datos...")
        
        # 1. Tabla Platforms
        try:
            db.session.execute(text("ALTER TABLE platforms ADD COLUMN visits INT DEFAULT 0"))
            db.session.commit()
            print("✅ Columna 'visits' añadida a 'platforms'")
        except Exception:
            db.session.rollback()
            print("ℹ️ Columna 'visits' ya existe o no pudo ser creada en 'platforms'")

        # Platform Branding and Identity
        cols_plat = [
            ("logo_url", "VARCHAR(255)"),
            ("bg_color", "VARCHAR(20) DEFAULT '#6366f1'"),
            ("text_color", "VARCHAR(20) DEFAULT '#ffffff'")
        ]
        
        for col, col_type in cols_plat:
            try:
                db.session.execute(text(f"ALTER TABLE platforms ADD COLUMN {col} {col_type}"))
                db.session.commit()
                print(f"✅ Columna '{col}' añadida a 'platforms'")
            except Exception:
                db.session.rollback()
                print(f"ℹ️ Columna '{col}' ya existe en 'platforms'")

        # Relationship Table: user_platforms (ensure it exists)
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_platforms (
                    user_id INTEGER NOT NULL,
                    platform_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, platform_id),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(platform_id) REFERENCES platforms(id)
                )
            """))
            db.session.commit()
            print("✅ Tabla 'user_platforms' verificada")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al verificar tabla 'user_platforms': {e}")

        # 3. Marcar tabla de Solicitudes (Asegurar user_email)
        try:
            db.session.execute(text("ALTER TABLE access_requests ADD COLUMN user_email VARCHAR(120)"))
            db.session.commit()
            print("✅ Columna 'user_email' añadida a 'access_requests'")
        except Exception:
            db.session.rollback()
            print("ℹ️ Columna 'user_email' ya existe en 'access_requests'")

        print("\n🚀 Sincronización finalizada.")

if __name__ == "__main__":
    sync_schema()
