import os
import sys
from dotenv import load_dotenv

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.modules.auth.models import User

def check_users():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print(f"\n--- DIAGNÓSTICO DE BASE DE DATOS ---")
        print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        users = User.query.all()
        print(f"Usuarios encontrados: {len(users)}")
        for u in users:
            print(f"- ID: {u.id} | Email: {u.email} | Rol: {u.role} | Origen: {u.auth_source}")
        print(f"------------------------------------\n")

if __name__ == '__main__':
    check_users()
