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
