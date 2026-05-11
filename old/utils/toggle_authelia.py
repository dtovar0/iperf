import os
import sys
import subprocess

# Archivo .env
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

def get_nginx_path():
    """Busca la ruta del Nginx en el archivo .env"""
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith("NGINX_CONF_PATH="):
                    return line.split("=")[1].strip()
    return "/etc/nginx/conf.d/vivaro.conf" # Valor por defecto

NGINX_CONF = get_nginx_path()

def toggle_nginx(enable=True):
    if not os.path.exists(NGINX_CONF):
        print(f"⚠️  No se encontró el archivo de Nginx en {NGINX_CONF}")
        return False

    try:
        with open(NGINX_CONF, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            # Líneas que controlamos en la sección de Authelia
            keywords = ["auth_request", "auth_request_set", "proxy_set_header Remote-", "error_page 401"]
            if any(key in line for key in keywords):
                clean_line = line.lstrip().lstrip('#').strip()
                if enable:
                    new_lines.append(f"        {clean_line}\n")
                else:
                    new_lines.append(f"        # {clean_line}\n")
            else:
                new_lines.append(line)

        with open(NGINX_CONF, 'w') as f:
            f.writelines(new_lines)
        
        print(f"✅ Nginx: Authelia {'HABILITADO' if enable else 'DESHABILITADO'}")
        subprocess.run(["sudo", "nginx", "-t"], check=True)
        subprocess.run(["sudo", "systemctl", "reload", "nginx"], check=True)
        return True
    except Exception as e:
        print(f"❌ Error modificando Nginx: {e}")
        return False

def toggle_env(enable=True):
    if not os.path.exists(ENV_FILE):
        print(f"⚠️  No se encontró el archivo .env en {ENV_FILE}")
        return False

    try:
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.startswith("AUTHELIA_ENABLED="):
                new_lines.append(f"AUTHELIA_ENABLED={'true' if enable else 'false'}\n")
            else:
                new_lines.append(line)

        with open(ENV_FILE, 'w') as f:
            f.writelines(new_lines)
        
        print(f"✅ .env: AUTHELIA_ENABLED={'true' if enable else 'false'}")
        return True
    except Exception as e:
        print(f"❌ Error modificando .env: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 toggle_authelia.py [on|off]")
        sys.exit(1)

    action = sys.argv[1].lower()
    enable = action == "on"

    print(f"\n🚀 Sincronizando Authelia Modo: {action.upper()}...")
    print("-" * 40)
    
    env_ok = toggle_env(enable)
    nginx_ok = toggle_nginx(enable)

    if env_ok and nginx_ok:
        print("-" * 40)
        print(f"✨ ¡Sistema Nexus {'Protegido por SSO' if enable else 'en Modo Local'} exitosamente!\n")
    else:
        print("\n⚠️  Hubo problemas en la sincronización. Revisa los permisos de sudo.\n")
