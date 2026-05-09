import subprocess
import re
import threading
import time
import socket
import json
import os
from datetime import datetime
from app import db
from app.modules.iperf.models import IperfSession, IperfMeasurement, IperfSessionSummary, IperfTest

class IperfService:
    _server_proc = None
    _client_proc = None
    _lock = threading.Lock()
    
    # Regex para capturar el valor y la unidad de bandwidth: [  5]   0.00-1.00   sec  1.12 GBytes  9.61 Gbits/sec
    DATA_RE = re.compile(
        r'\[(?P<id>\s*\d+|SUM)\]\s+'
        r'(?P<t0>\d+\.\d+)-(?P<t1>\d+\.\d+)\s+sec\s+'
        r'[\d.]+\s+\w+Bytes\s+'
        r'(?P<rate>[\d.]+)\s+(?P<unit>G|M|K)bits/sec'
        r'(?:\s+(?P<jitter>[\d.]+)\s+ms)?'
        r'(?:\s+(?P<lost>\d+)/\d+)?'
        r'.*?(?:\s+(?P<role>sender|receiver))?$'
    )
    SEP_RE = re.compile(r'^[\s\-]+$')
    LISTENING_RE = re.compile(r'Server listening on')
    ACCEPTED_RE = re.compile(r'Accepted connection from')

    @staticmethod
    def _to_gbps(v, u):
        return {"G": v, "M": v / 1000, "K": v / 1000000}[u]

    @staticmethod
    def _iperf3_reader(proc, mode, session_id, app):
        """Lee stdout de iperf3 en tiempo real y guarda en DB."""
        group = {"lines": [], "has_sum": False, "sum_data": None}
        log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"

        def commit_measurement(data):
            with app.app_context():
                try:
                    meas = IperfMeasurement(
                        session_id=session_id,
                        gbps=data["gbps"],
                        jitter_ms=data["jitter"] or 0,
                        retransmits=data["retx"]
                    )
                    db.session.add(meas)
                    db.session.commit()
                except Exception as e:
                    print(f"[DB Error] {e}")

        def flush_group():
            if group["has_sum"] and group["sum_data"]:
                commit_measurement(group["sum_data"])
            elif group["lines"]:
                commit_measurement(group["lines"][-1])
            group["lines"].clear()
            group["has_sum"] = False
            group["sum_data"] = None

        for raw in proc.stdout:
            line = raw.rstrip()
            if not line: continue
            
            # Escribir en el archivo de logs para el dashboard live
            with open(log_path, 'a') as f:
                f.write(f"{line}\n")

            # Detección de eventos (solo para el log/UI, la sesión ya está creada)
            if mode == "server":
                if IperfService.ACCEPTED_RE.search(line):
                    # Podríamos marcar la sesión como activa aquí si fuera necesario
                    pass
                if IperfService.LISTENING_RE.search(line):
                    # Fin de una conexión de cliente
                    pass

            if IperfService.SEP_RE.match(line):
                flush_group()
                continue

            m = IperfService.DATA_RE.search(line)
            if not m: continue

            sid = m.group("id").strip()
            gbps = IperfService._to_gbps(float(m.group("rate")), m.group("unit"))
            jitter = float(m.group("jitter")) if m.group("jitter") else None
            retx = int(m.group("lost")) if m.group("lost") else 0
            role = m.group("role") or ""
            data = {"gbps": gbps, "jitter": jitter, "retx": retx}

            if mode == "client" and role == "receiver": continue
            if mode == "server" and role == "sender": continue

            if sid == "SUM":
                group["has_sum"] = True
                group["sum_data"] = data
            else:
                group["lines"].append(data)
        
        flush_group()
        
        # Al finalizar el lector (proceso cerrado), calculamos el resumen
        with app.app_context():
            IperfService._finalize_session(session_id)

    @staticmethod
    def _finalize_session(session_id):
        """Calcula el resumen de la sesión y la cierra."""
        session = IperfSession.query.get(session_id)
        if not session: return

        session.status = 'completed'
        session.ended_at = datetime.utcnow()
        
        measurements = IperfMeasurement.query.filter_by(session_id=session_id).all()
        if measurements:
            vals = [m.gbps for m in measurements]
            jitters = [m.jitter_ms for m in measurements]
            retxs = [m.retransmits for m in measurements]
            
            summary = IperfSessionSummary(
                session_id=session_id,
                avg_gbps=sum(vals) / len(vals),
                max_gbps=max(vals),
                min_gbps=min(vals),
                avg_jitter_ms=sum(jitters) / len(jitters),
                total_retransmits=sum(retxs),
                total_samples=len(vals)
            )
            db.session.add(summary)
        
        db.session.commit()

    @staticmethod
    def start_server(port=5201):
        """Inicia el servidor iperf3 y registra la sesión."""
        from flask import current_app
        app = current_app._get_current_object()
        
        if IperfService.is_server_running():
            return True, "Servidor ya está activo."

        try:
            # Crear sesión en DB
            new_session = IperfSession(
                mode='server',
                port=port,
                protocol='tcp', # Por defecto
                status='running'
            )
            db.session.add(new_session)
            db.session.commit()

            # Limpiar logs
            log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w') as f:
                f.write(f"--- Servidor Nexus iniciado a las {datetime.now()} ---\n")

            IperfService._server_proc = subprocess.Popen(
                ["iperf3", "-s", "-p", str(port), "--forceflush"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            
            thread = threading.Thread(
                target=IperfService._iperf3_reader, 
                args=(IperfService._server_proc, "server", new_session.id, app),
                daemon=True
            )
            thread.start()
            
            return True, "Servidor iperf3 iniciado correctamente."
        except Exception as e:
            return False, f"Error al iniciar servidor: {str(e)}"

    @staticmethod
    def stop_server():
        """Detiene el proceso del servidor."""
        if IperfService._server_proc:
            IperfService._server_proc.terminate()
            IperfService._server_proc = None
            
        # Limpieza agresiva de procesos huérfanos
        subprocess.run(['pkill', '-9', 'iperf3'], capture_output=True)
        subprocess.run(['fuser', '-k', '5201/tcp'], capture_output=True)
        
        return True, "Servidor detenido correctamente."

    @staticmethod
    def is_server_running():
        """Verifica si el proceso está activo y el puerto ocupado."""
        if IperfService._server_proc and IperfService._server_proc.poll() is None:
            return True
        
        # Verificar puerto
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", 5201)) == 0

    @staticmethod
    def run_test_async(test_id, app):
        """Mantiene compatibilidad con la interfaz anterior de IperfTest."""
        thread = threading.Thread(target=IperfService._execute_client_test, args=(test_id, app))
        thread.start()

    @staticmethod
    def _execute_client_test(test_id, app):
        """Ejecuta un test de cliente iperf3."""
        with app.app_context():
            test = IperfTest.query.get(test_id)
            if not test: return

            test.status = 'running'
            test.started_at = datetime.utcnow()
            db.session.commit()

            # Crear sesión avanzada vinculada
            new_session = IperfSession(
                mode='client',
                host=test.target_host,
                port=test.port,
                protocol=test.protocol.lower(),
                duration_s=test.duration,
                status='running',
                user_id=test.user_id
            )
            db.session.add(new_session)
            db.session.commit()

            cmd = ["iperf3", "-c", test.target_host, "-p", str(test.port),
                   "-t", str(test.duration), "--forceflush", "-i", "1"]
            if test.protocol.lower() == 'udp':
                cmd += ["-u", "-b", "100M"]

            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1
                )
                # El lector se encargará de guardar las mediciones y cerrar la sesión
                IperfService._iperf3_reader(proc, "client", new_session.id, app)
                
                test.status = 'completed'
                test.results_json = json.dumps({"session_id": new_session.id})
            except Exception as e:
                test.status = 'failed'
                test.error_message = str(e)
            
            test.finished_at = datetime.utcnow()
            db.session.commit()
