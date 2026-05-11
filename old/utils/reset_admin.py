import sys
import os

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.modules.auth.models import User

def reset_admin():
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print("🔐 NEXUS - RESTABLECIMIENTO DE USUARIO ADMINISTRADOR")
        print("="*60)

        email = input("Introduce el email (por defecto 'admin'): ") or 'admin'
        admin = User.query.filter_by(email=email).first()

        if not admin:
            print(f"❌ El usuario '{email}' no existe.")
            create = input(f"¿Deseas crear al usuario '{email}' como administrador? (si/no): ")
            if create.lower() == 'si':
                admin = User(email=email, nombre=email, role='administrador')
                password = input("Introduce la nueva contraseña: ")
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()
                print(f"✅ Usuario '{email}' creado exitosamente.")
            else:
                return
        else:
            password = input("Introduce la nueva contraseña: ")
            admin.set_password(password)
            admin.auth_source = 'local' # Forzar origen local para recuperar acceso manual
            db.session.commit()
            print(f"✅ Contraseña y origen de autenticación para '{email}' actualizados exitosamente.")

        print("="*60 + "\n")

if __name__ == '__main__':
    reset_admin()
