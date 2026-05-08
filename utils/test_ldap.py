import sys
import os

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.modules.auth.models import AuthConfig
from app.modules.auth.services import validate_ldap_connection

def test_ldap():
    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("🔍 PRUEBA DE CONECTIVIDAD LDAP")
        print("="*60)

        config = AuthConfig.query.first()
        if not config:
            print("❌ Error: No hay configuración LDAP en la base de datos.")
            return

        print(f"📡 Intentando conectar a: {config.ldap_host}:{config.ldap_port}")
        print(f"👤 Usuario Bind: {config.ldap_user}")
        
        success, msg = validate_ldap_connection()
        
        if success:
            print("\n✅ RESULTADO: CONEXIÓN EXITOSA")
            print(f"📝 Detalle: {msg}")
        else:
            print("\n❌ RESULTADO: FALLO DE CONEXIÓN")
            print(f"📝 Error: {msg}")
            print("\n💡 Tip: Verifica el Host, Puerto y las credenciales de Bind.")

        print("="*60 + "\n")

if __name__ == '__main__':
    test_ldap()
