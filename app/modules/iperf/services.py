import iperf3
import subprocess
import json
import threading
import time
from datetime import datetime
from app import db
from app.modules.iperf.models import IperfTest

class IperfService:
    _server_thread = None
    _stop_server_flag = False

    @staticmethod
    def run_test_async(test_id, app):
        """Inicia la ejecución de iperf3 en un hilo separado."""
        thread = threading.Thread(target=IperfService._execute_test, args=(test_id, app))
        thread.start()

    @staticmethod
    def _execute_test(test_id, app):
        """Lógica de ejecución del comando iperf3."""
        with app.app_context():
            test = IperfTest.query.get(test_id)
            if not test:
                return

            test.status = 'running'
            test.started_at = datetime.utcnow()
            db.session.commit()

            try:
                # Usar la librería iperf3 en lugar del comando de sistema
                client = iperf3.Client()
                client.server_hostname = test.target_host
                client.port = test.port
                client.duration = test.duration
                client.protocol = test.protocol.lower() # 'tcp' o 'udp'
                
                # Ejecutar el test (bloqueante en este hilo)
                result = client.run()
                
                if result.error:
                    test.error_message = result.error
                    test.status = 'failed'
                else:
                    # Guardar los resultados en formato JSON
                    # result.json es un diccionario con toda la data de iperf3
                    test.results_json = json.dumps(result.json)
                    test.status = 'completed'

            except Exception as e:
                test.error_message = f"Excepción en iperf3-python: {str(e)}"
                test.status = 'failed'
            
            test.finished_at = datetime.utcnow()
            db.session.commit()

    @staticmethod
    def is_server_running():
        """Verifica si el hilo del servidor está activo o si el puerto está ocupado."""
        if IperfService._server_thread and IperfService._server_thread.is_alive():
            return True
        
        # Fallback: Verificar si hay algún proceso iperf3 (binario) corriendo
        try:
            output = subprocess.check_output(['pgrep', '-f', 'iperf3'], text=True)
            return True if output.strip() else False
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def _server_loop(port, log_path):
        """Bucle del servidor que se ejecuta en un hilo secundario."""
        while not IperfService._stop_server_flag:
            try:
                server = iperf3.Server()
                server.port = port
                # El método run() bloquea hasta que un cliente se conecta y termina el test
                result = server.run()
                
                if result and log_path:
                    with open(log_path, 'a') as f:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        # Formatear una línea que el frontend pueda parsear mediante regex
                        # Ejemplo: [ 5] 0.00-10.00 sec 1.25 GBytes 10.7 Gbits/sec
                        mbps = result.received_Mbps
                        gbps = mbps / 1000
                        f.write(f"[{timestamp}] Test finalizado. Bandwidth: {gbps:.2f} Gbits/sec\n")
                        f.write(f"[{timestamp}] JSON: {json.dumps(result.json)}\n")
            except Exception as e:
                if not IperfService._stop_server_flag:
                    with open(log_path, 'a') as f:
                        f.write(f"[{datetime.now()}] Error en el servidor: {str(e)}\n")
                    time.sleep(1)

    @staticmethod
    def start_server():
        """Inicia el servidor iperf3 usando la librería en un hilo de fondo."""
        try:
            # Detener cualquier instancia previa
            IperfService.stop_server()
            
            log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"
            
            # Limpiar/Inicializar logs
            with open(log_path, 'a') as f:
                f.write(f"\n--- Servidor iniciado con iperf3-python a las {datetime.now()} ---\n")
            
            IperfService._stop_server_flag = False
            IperfService._server_thread = threading.Thread(
                target=IperfService._server_loop, 
                args=(5201, log_path),
                daemon=True
            )
            IperfService._server_thread.start()
            
            return True, f"Servidor iniciado correctamente (vía librería). Logs en {log_path}"
        except Exception as e:
            return False, f"Error al iniciar servidor: {str(e)}"

    @staticmethod
    def stop_server():
        """Detiene el hilo del servidor y limpia procesos/puertos."""
        try:
            IperfService._stop_server_flag = True
            
            # Matar procesos binarios si existen
            subprocess.run(['pkill', '-9', 'iperf3'], capture_output=True)
            
            # Liberar el puerto agresivamente
            subprocess.run(['fuser', '-k', '5201/tcp'], capture_output=True)
            
            time.sleep(0.5)
            return True, "Servidor detenido y puerto liberado"
        except Exception as e:
            return False, f"Error al detener servidor: {str(e)}"
