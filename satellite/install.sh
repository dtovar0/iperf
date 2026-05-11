#!/bin/bash

# Nexus Iperf Satellite Installer
# Usage: sudo ./install.sh [API_TOKEN]

set -e

if [[ $EUID -ne 0 ]]; then
   echo "Este script debe ejecutarse como root (sudo)." 
   exit 1
fi

TOKEN=${1:-"nexus_secret_token_2024_v1"}
INSTALL_DIR="/opt/nexus-satellite"
USER_NAME="nexus-agent"

echo "🚀 Iniciando instalación de Nexus Satellite Agent..."

# 1. Instalar dependencias del sistema
echo "📦 Instalando dependencias (iperf3, python3)..."
apt-get update && apt-get install -y iperf3 python3-venv python3-pip psmisc

# 2. Crear usuario y directorio
if ! id "$USER_NAME" &>/dev/null; then
    useradd -m -s /bin/bash "$USER_NAME"
fi

mkdir -p "$INSTALL_DIR"
cp agent.py "$INSTALL_DIR/"
chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR"

# 3. Preparar entorno virtual
echo "venv"
cd "$INSTALL_DIR"
sudo -u "$USER_NAME" python3 -m venv venv
sudo -u "$USER_NAME" ./venv/bin/pip install flask requests python-dotenv

# 4. Configurar .env
echo "IPERF_API_TOKEN=$TOKEN" > .env
echo "SATELLITE_NAME=$(hostname)" >> .env
chown "$USER_NAME:$USER_NAME" .env

# 5. Crear servicio systemd
echo "⚙️ Configurando servicio systemd..."
cat <<EOF > /etc/systemd/system/nexus-satellite.service
[Unit]
Description=Nexus Iperf Satellite Agent
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Iniciar servicio
systemctl daemon-reload
systemctl enable nexus-satellite
systemctl restart nexus-satellite

echo "✅ Instalación completada!"
echo "📡 El agente está corriendo en el puerto 5001"
echo "🔑 Token de API configurado: $TOKEN"
echo "------------------------------------------------"
echo "Prueba de conexión: curl -H 'X-API-Token: $TOKEN' http://localhost:5001/api/status"
