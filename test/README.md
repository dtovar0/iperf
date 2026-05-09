# iperf3 Dashboard — Web en vivo

## Instalación

```bash
pip install -r requirements.txt
# Linux/macOS: también necesitas iperf3 en el sistema
sudo apt install iperf3        # Debian/Ubuntu
brew install iperf3            # macOS
```

## Uso

1. Levanta un servidor iperf3 en el host destino:
   ```bash
   iperf3 -s
   ```

2. En `app.py`, reemplaza `simulate_measurement()` con la medición real:
   ```python
   import iperf3

   SERVER_HOST = "192.168.1.100"   # ← cambia aquí
   SERVER_PORT = 5201

   def simulate_measurement():
       client = iperf3.Client()
       client.server_hostname = SERVER_HOST
       client.port            = SERVER_PORT
       client.duration        = 1
       client.protocol        = 'tcp'   # o 'udp' para obtener jitter
       result = client.run()
       return {
           'sent':        result.sent_Mbps,
           'recv':        result.received_Mbps,
           'jitter':      getattr(result, 'jitter_ms', 0),
           'retransmits': getattr(result, 'retransmits', 0),
       }
   ```

3. Ejecuta la app:
   ```bash
   python app.py
   ```

4. Abre el navegador en **http://localhost:8050**

## Notas
- El dashboard corre en modo simulación por defecto (sin necesitar servidor real).
- Presiona **▶ Iniciar** para comenzar las mediciones.
- El protocolo UDP da datos de jitter; TCP da retransmisiones.
