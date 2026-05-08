from app import create_app, db
from app.modules.auth.models import User
import sys

def seed_users():
    app = create_app()
    with app.app_context():
        print("🌱 Iniciando sembrado de usuarios profesionales...")
        
        # Definición de datos profesionales
        demo_users = [
            { 'email': 'admin', 'name': 'Administrador Principal', 'role': 'admin', 'active': True },
            { 'email': 'dtovar', 'name': 'Daniel Tovar', 'role': 'admin', 'active': True },
            { 'email': 'schen', 'name': 'Sarah Chen', 'role': 'user', 'active': True },
            { 'email': 'mrosso', 'name': 'Marco Rosso', 'role': 'user', 'active': True },
            { 'email': 'anovak', 'name': 'Alex Novak', 'role': 'Audit Compliance', 'active': False },
            { 'email': 'engine', 'name': 'Service Engine', 'role': 'System', 'active': True },
            { 'email': 'auditor', 'name': 'External Auditor', 'role': 'Guest', 'active': False }
        ]

        for data in demo_users:
            # Verificar si ya existe para evitar duplicados
            existing = User.query.filter_by(email=data['email']).first()
            if not existing:
                user = User(
                    email=data['email'],
                    nombre=data['name'],
                    role=data['role'],
                    is_active=data['active']
                )
                user.set_password('Nexus2024!')
                db.session.add(user)
                print(f"✅ Usuario creado: {data['name']} ({data['role']})")
            else:
                print(f"⚠️ El usuario {data['name']} ya existe. Omitiendo.")

        try:
            db.session.commit()
            print("\n✨ Sembrado completado con éxito.")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error durante el sembrado: {str(e)}")

if __name__ == "__main__":
    seed_users()
