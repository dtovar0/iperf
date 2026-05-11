import sys
import os

# Añadir el raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform, AccessRequest
from app.modules.audit.models import AuditLog
from sqlalchemy import text

def reset_and_seed():
    app = create_app()
    with app.app_context():
        print("🧹 Iniciando purga total de la base de datos...")
        try:
            # Deshabilitar FKs para limpieza profunda (MySQL Syntax)
            db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            tables = [
                'user_areas', 'user_platforms', 'user_favorites',
                'access_requests', 'platforms', 'areas', 'audit_logs', 'users'
            ]
            
            for table in tables:
                # Verificar si la tabla existe antes de borrar
                db.session.execute(text(f"DELETE FROM {table};"))
                print(f"  - {table} purgada.")
            
            db.session.commit()
            print("✨ Base de datos limpia.")

            # 1. Recrear Admin
            print("\n👤 Creando usuario administrador...")
            admin = User(
                email='admin@nexus.com',
                nombre='Nexus Admin',
                role='administrador',
                auth_source='local',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # 2. Sembrar Áreas
            print("\n🏢 Sembrando Áreas...")
            areas = [
                Area(name='Ciberseguridad', icon='shield-alt', color='#f43f5e', description='Protección de activos críticos y respuesta a incidentes.'),
                Area(name='Infraestructura Cloud', icon='cloud', color='#0ea5e9', description='Gestión de recursos en la nube y servidores.'),
                Area(name='Desarrollo & DevOps', icon='code', color='#8b5cf6', description='Ciclo de vida de software y automatización.')
            ]
            for a in areas:
                db.session.add(a)
            db.session.flush() # Obtener IDs

            # 3. Sembrar Plataformas
            print("\n🚀 Sembrando Plataformas...")
            platforms = [
                # Seguridad
                Platform(name='Nexus Guard', area_id=areas[0].id, icon='lock', bg_color='#f43f5e', 
                         description='Consola central de gestión de identidades y accesos privilegiados.'),
                Platform(name='CrowdStrike EDR', area_id=areas[0].id, icon='user-shield', bg_color='#e11d48', 
                         description='Detección y respuesta en endpoints de última generación.'),
                # Cloud
                Platform(name='AWS Console', area_id=areas[1].id, icon='server', bg_color='#0ea5e9', 
                         description='Gestión centralizada de recursos en Amazon Web Services.'),
                Platform(name='Google Cloud Platform', area_id=areas[1].id, icon='network-wired', bg_color='#3b82f6', 
                         description='Ecosistema de servicios escalables en Google Cloud.'),
                # DevOps
                Platform(name='GitLab Nexus', area_id=areas[2].id, icon='gitlab', bg_color='#8b5cf6', 
                         description='Control de versiones y pipelines de CI/CD para el portal.'),
                Platform(name='Grafana Dashboard', area_id=areas[2].id, icon='chart-line', bg_color='#a855f7', 
                         description='Visualización de métricas y observabilidad del ecosistema.')
            ]
            for p in platforms:
                db.session.add(p)

            db.session.commit()
            
            # Habilitar FKs
            db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            db.session.commit()
            
            print("\n✅ SISTEMA RESTAURADO CON ÉXITO")
            print("Usuario: admin@nexus.com / admin123")
            print(f"Áreas: {len(areas)}")
            print(f"Plataformas: {len(platforms)}")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error crítico: {str(e)}")

if __name__ == '__main__':
    reset_and_seed()
