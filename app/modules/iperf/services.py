import subprocess
import json
import threading
from datetime import datetime
from app import db
from app.modules.iperf.models import IperfTest

class IperfService:
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
                # Construir comando iperf3 -J (JSON output)
                cmd = [
                    'iperf3', 
                    '-c', test.target_host, 
                    '-p', str(test.port), 
                    '-t', str(test.duration),
                    '-J'
                ]
                
                if test.protocol == 'UDP':
                    cmd.append('-u')

                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0 or process.stdout:
                    try:
                        # Validar si es JSON válido
                        json.loads(process.stdout)
                        test.results_json = process.stdout
                        test.status = 'completed'
                    except json.JSONDecodeError:
                        test.error_message = "Error al decodificar JSON de iperf3: " + process.stdout[:500]
                        test.status = 'failed'
                else:
                    test.error_message = process.stderr or "Error desconocido al ejecutar iperf3"
                    test.status = 'failed'

            except Exception as e:
                test.error_message = str(e)
                test.status = 'failed'
            
            test.finished_at = datetime.utcnow()
            db.session.commit()

    @staticmethod
    def is_server_running():
        """Verifica si hay un proceso iperf3 -s en ejecución."""
        try:
            # Buscamos procesos que tengan 'iperf3' y '-s'
            output = subprocess.check_output(['pgrep', '-f', 'iperf3 -s'], text=True)
            return True if output.strip() else False
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def start_server():
        """Detiene cualquier instancia previa e inicia el servidor iperf3 -s."""
        try:
            # Siempre intentamos detener procesos previos para evitar conflictos de puerto
            IperfService.stop_server()
            
            log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"
            # Asegurar que el comando use un archivo de log
            subprocess.Popen(['iperf3', '-s', '-D', '--logfile', log_path])
            return True, f"Server (re)started successfully. Logging to {log_path}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def stop_server():
        """Detiene el servidor iperf3."""
        try:
            subprocess.run(['pkill', '-f', 'iperf3 -s'])
            return True, "Server stopped"
        except Exception as e:
            return False, str(e)
