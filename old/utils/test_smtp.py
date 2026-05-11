import sys
import os

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.modules.notifications.models import SMTPConfig
from app.modules.notifications.services import send_test_email

def test_smtp():
    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("📧 PRUEBA DE ENVÍO SMTP")
        print("="*60)

        config = SMTPConfig.query.first()
        if not config:
            print("❌ Error: No hay configuración SMTP en la base de datos.")
            return

        print(f"📡 Servidor: {config.server}:{config.port}")
        print(f"🔐 Cifrado: {config.encryption}")
        print(f"👤 Remitente: {config.sender_name} <{config.username}>")
        
        dest = input("\nIntroduce el correo de destino para la prueba: ")
        if not dest:
            print("Operación cancelada.")
            return

        print(f"🚀 Enviando correo de prueba a {dest}...")
        success, msg = send_test_email(dest)

        if success:
            print("\n✅ RESULTADO: CORREO ENVIADO EXITOSAMENTE")
            print(f"📝 Transacción: {msg}")
        else:
            print("\n❌ RESULTADO: FALLO EN EL ENVÍO")
            print(f"📝 Error: {msg}")
            print("\n💡 Tip: Verifica el puerto (587 para TLS) y si tu proveedor requiere 'Apps de terceros' (ej. Gmail).")

        print("="*60 + "\n")

if __name__ == '__main__':
    test_smtp()
