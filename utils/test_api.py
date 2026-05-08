import requests
import os
import sys
from dotenv import load_dotenv

# Añadir directorio raíz al path para posibles imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_api():
    """
    Script táctico para validar la integridad de la NEXUS API (v1).
    Verifica conectividad, autenticación y endpoints principales.
    """
    load_dotenv()
    
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    api_token = os.getenv('API_TOKEN')
    
    print("\n" + "="*50)
    print(" 🛠️  VALIDADOR DE NEXUS API TÁCTICA ")
    print("="*50)
    
    if not api_token:
        print("❌ ERROR: API_TOKEN no configurado en el archivo .env")
        return
    
    headers = {"X-API-TOKEN": api_token}
    
    # 1. Test Endpoint: STATUS
    print(f"\n[1/3] Verificando salud del sistema ({base_url}/api/v1/status)...")
    try:
        r = requests.get(f"{base_url}/api/v1/status", headers=headers, timeout=5)
        if r.status_code == 200:
            print(f"✅ OK: {r.json().get('message')}")
        else:
            print(f"❌ FALLO: Código {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")

    # 2. Test Endpoint: AUTH (Probando token inválido)
    print("\n[2/3] Verificando seguridad (Token inválido)...")
    try:
        r = requests.get(f"{base_url}/api/v1/tasks", headers={"X-API-TOKEN": "token_falso"}, timeout=5)
        if r.status_code == 401:
            print("✅ OK: El sistema bloqueó el acceso no autorizado correctamente.")
        else:
            print(f"⚠️  ALERTA: El sistema no bloqueó el acceso (Status: {r.status_code})")
    except Exception as e:
        print(f"❌ ERROR: {e}")

    # 3. Test Endpoint: TASKS (Listado)
    print("\n[3/3] Recuperando historial táctico (/api/v1/tasks)...")
    try:
        r = requests.get(f"{base_url}/api/v1/tasks?limit=5", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            count = data.get('count', 0)
            print(f"✅ OK: Se recuperaron {count} tareas exitosamente.")
            if count > 0:
                last_task = data['data'][0]
                print(f"   > Última tarea: ID #{last_task['id']} | Estado: {last_task['estado']}")
        else:
            print(f"❌ FALLO: {r.text}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

    print("\n" + "="*50)
    print(" ✅ VALIDACIÓN FINALIZADA ")
    print("="*50 + "\n")

if __name__ == "__main__":
    validate_api()
