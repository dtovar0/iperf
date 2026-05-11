import os
import sys
from dotenv import load_dotenv

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.modules.auth.models import User

def emergency_reset():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print("🛠️ INICIANDO RESET DE EMERGENCIA...")
        
        # Buscar usuario admin (por email o por nombre)
        admin = User.query.filter_by(email='admin').first()
        
        if admin:
            db.session.delete(admin)
            db.session.commit()
            print("🗑️ Usuario admin antiguo eliminado.")
            
        # Crear usuario admin fresco
        new_admin = User(
            email='admin',
            nombre='Administrador Maestro',
            role='administrador',
            auth_source='local',
            is_active=True
        )
        new_admin.set_password('admin123')
        
        db.session.add(new_admin)
        db.session.commit()
        
        print("✅ Usuario 'admin' recreado exitosamente.")
        print("🔑 Credenciales: admin / admin123")
        print("🌐 Origen: LOCAL")

if __name__ == '__main__':
    emergency_reset()
