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
from app.modules.iperf.dashboard_v2.state import timestamps, recv_mbps, jitter_ms, retransmits, log_lines, lock as state_lock
class IperfService:
    _active_procs = {} # session_id -> subprocess.Popen
    _lock = threading.Lock()
    _live_data = {}    # Mantener para compatibilidad si es necesario, pero priorizar state.py
    _notified_sessions = set() # ids de sesiones ya notificadas
    DATA_RE = re.compile(
        r'\[\s*(?P<id>\d+|SUM)\]\s+'
        r'(?P<t0>[\d.]+)-(?P<t1>[\d.]+)\s+sec\s+'
        r'[\d.]+\s+\w+Bytes\s+'
        r'(?P<rate>[\d.]+)\s+(?P<unit>[GkMK])bits/sec'
        r'(?:\s+(?P<jitter>[\d.]+)\s+ms)?'           # Jitter (UDP)
        r'(?:\s+(?P<lost>\d+)/\s*(?P<total>\d+))?'   # Perdidos (UDP)
        r'(?:\s+(?P<retx>\d+))?'                     # Retransmisiones (TCP)
        r'.*?(?:\s+(?P<role>sender|receiver))?\s*$'
    )
    SEP_RE       = re.compile(r'^[\s\-]+$')
    LISTENING_RE = re.compile(r'Server listening on')
    ACCEPTED_RE  = re.compile(r'Accepted connection from')

    @staticmethod
    def _to_gbps(v, u):
        return {"G": v, "M": v / 1000, "K": v / 1000000}[u]

    @staticmethod
    def port_is_listening(port: int) -> bool:
        """Verifica si hay algo escuchando en el puerto TCP dado."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0

    @staticmethod
    def _iperf3_reader(proc, mode, session_id, app, user_id=None):
        """
        Lector 1:1 con test/app.py.
        Actualiza tanto la DB como los deques globales del dashboard.
        Inyecta cabeceras de columnas cada 5 steps.
        """
        group = {"lines": [], "has_sum": False, "sum_data": None}
        current_db_session_id = session_id 
        
        # Variables para repetición de cabeceras
        header_line = None
        step_counter = 0
        last_t1 = -1

        def commit(data, active_sid):
            ts = time.strftime('%H:%M:%S')
            # 1. Actualizar estado global para el dashboard (Dash)
            with state_lock:
                timestamps.append(ts)
                recv_mbps.append(round(data["gbps"] * 1000, 2)) # Guardar en Mbps para consistencia con test/app.py
                jitter_ms.append(round(data["jitter"], 3))
                retransmits.append(data["retx"])

            # 2. Persistencia en DB (Nexus Logic)
            if active_sid:
                with app.app_context():
                    try:
                        meas = IperfMeasurement(
                            session_id=active_sid,
                            gbps=data["gbps"],
                            jitter_ms=data["jitter"],
                            retransmits=data["retx"]
                        )
                        db.session.add(meas)
                        db.session.commit()
                    except Exception as e:
                        print(f"Error persisting measurement: {e}")
            
            # 3. Sincronización con el historial de sesión (Panel Cliente)
            if active_sid in IperfService._live_data:
                IperfService._live_data[active_sid]["measurements"].append({
                    "gbps": data["gbps"], 
                    "jitter": data["jitter"], 
                    "retx": data["retx"],
                    "ts": ts,
                    "t1": data.get("t1", 0)
                })

        def flush_interval(active_sid):
            if group["has_sum"]:
                commit(group["sum_data"], active_sid)
            elif group["lines"]:
                commit(group["lines"][-1], active_sid)
            group["lines"].clear()
            group["has_sum"] = False
            group["sum_data"] = None

        for raw in proc.stdout:
            line = raw.rstrip()
            if not line: continue
            
            # --- Lógica de repetición de cabeceras ---
            if "Interval" in line and "Bitrate" in line:
                header_line = line
            
            m_data = IperfService.DATA_RE.search(line)
            if m_data:
                try:
                    t0, t1 = float(m_data.group("t0")), float(m_data.group("t1"))
                    # Solo contar intervalos reales de ~1s
                    if 0.5 <= (t1 - t0) <= 1.5:
                        if t1 != last_t1:
                            last_t1 = t1
                            step_counter += 1
                            # Cada 10 steps (intervalos), inyectar cabecera antes de la siguiente línea
                            if step_counter > 1 and (step_counter - 1) % 10 == 0 and header_line:
                                with state_lock:
                                    log_lines.append(header_line)
                                if current_db_session_id in IperfService._live_data:
                                    IperfService._live_data[current_db_session_id]["logs"].append(header_line)
                except Exception:
                    pass
            # ----------------------------------------

            with state_lock:
                log_lines.append(line)
            
            # Asegurar que los logs lleguen a _live_data para el panel de cliente
            if current_db_session_id in IperfService._live_data:
                IperfService._live_data[current_db_session_id]["logs"].append(line)

            # Detección de eventos de sesión
            if mode == "server":
                if IperfService.ACCEPTED_RE.search(line):
                    flush_interval(current_db_session_id)
                    from app.modules.iperf.dashboard_v2.state import clear_buffers
                    clear_buffers()
                    with app.app_context():
                        try:
                            new_s = IperfSession(
                                mode='server', port=5201, 
                                status='running', user_id=user_id,
                                started_at=datetime.utcnow()
                            )
                            db.session.add(new_s)
                            db.session.commit()
                            current_db_session_id = new_s.id
                            # Inicializar logs para la nueva sesión
                            IperfService._live_data[current_db_session_id] = {"measurements": [], "summary": None, "logs": []}
                        except Exception as e:
                            print(f"Error starting server session: {e}")
                    continue

                if IperfService.LISTENING_RE.search(line):
                    flush_interval(current_db_session_id)
                    if current_db_session_id:
                        with app.app_context():
                            try:
                                s = IperfSession.query.get(current_db_session_id)
                                if s and s.status == 'running':
                                    s.status = 'completed'
                                    s.ended_at = datetime.utcnow()
                                    db.session.commit()
                            except Exception as e:
                                print(f"Error ending server session: {e}")
                    continue

            if IperfService.SEP_RE.match(line):
                flush_interval(current_db_session_id)
                continue

            m = IperfService.DATA_RE.search(line)
            if not m: continue
            
            # Validación de intervalo (1:1 con test/app.py)
            t0, t1 = float(m.group("t0")), float(m.group("t1"))
            if (t1 - t0) < 0.5 or (t1 - t0) > 1.5: continue

            gbps   = IperfService._to_gbps(float(m.group("rate")), m.group("unit"))
            jitter = float(m.group("jitter")) if m.group("jitter") else 0.0
            retx   = int(m.group("retx") or m.group("lost") or 0)
            role   = m.group("role") or ""
            data   = {
                "gbps": gbps, "jitter": jitter, "retx": retx,
                "ts": time.strftime('%H:%M:%S'), "t1": t1
            }

            if role:
                if mode == "client" and role == "receiver": continue
                if mode == "server" and role == "sender": continue

            if m.group("id").strip() == "SUM":
                group["has_sum"] = True
                group["sum_data"] = data
            else:
                group["lines"].append(data)
        
        flush_interval(current_db_session_id)
        
        # FINALIZACIÓN: Persistir resumen y estado final (Nexus Business Rules)
        if current_db_session_id:
            with app.app_context():
                try:
                    s = IperfSession.query.get(current_db_session_id)
                    if s:
                        # Si fue terminado por el sistema o natural
                        if s.status == 'running':
                            s.status = 'completed'
                        
                        s.ended_at = datetime.utcnow()
                        
                        # Guardar Resumen (si hay mediciones)
                        live_data = IperfService._live_data.get(current_db_session_id)
                        if live_data and live_data["measurements"]:
                            meas = live_data["measurements"]
                            vals = [m["gbps"] for m in meas]
                            jitters = [m["jitter"] for m in meas]
                            retxs = [m["retx"] for m in meas]
                            
                            summary = IperfSessionSummary(
                                session_id=s.id,
                                avg_gbps=sum(vals) / len(vals),
                                max_gbps=max(vals),
                                min_gbps=min(vals),
                                avg_jitter_ms=sum(jitters) / len(jitters),
                                total_retransmits=sum(retxs),
                                total_samples=len(vals)
                            )
                            db.session.add(summary)
                            # Marcar para que el frontend sepa que hay resumen nuevo
                            live_data["summary"] = summary.to_dict()
                            
                        db.session.commit()
                except Exception as e:
                    print(f"Error finalizing session {current_db_session_id}: {e}")

        IperfService._finalize_session_memory(current_db_session_id)

    @staticmethod
    def _finalize_session_memory(session_id):
        data = IperfService._live_data.get(session_id)
        if not data or not data["measurements"]: return
        meas = data["measurements"]
        vals = [m["gbps"] for m in meas]
        jitters = [m["jitter"] for m in meas]
        data["summary"] = {
            "avg_gbps": sum(vals) / len(vals),
            "max_gbps": max(vals),
            "min_gbps": min(vals),
            "avg_jitter_ms": sum(jitters) / len(jitters),
            "total_samples": len(vals)
        }
        # Limpiar tracking de proceso
        IperfService._active_procs.pop(session_id, None)

    @staticmethod
    def start_server(user_id, port=5201):
        """Levanta iperf3 -s con validación de concurrencia y limpieza agresiva (Rule #11)."""
        from flask import current_app
        from app.modules.auth.models import User
        app = current_app._get_current_object()
        
        # 1. Validar si otro usuario está usando este puerto en la APP
        existing_session = IperfSession.query.filter_by(status='running', port=port, mode='server').first()
        if existing_session and existing_session.user_id != user_id:
            owner = User.query.get(existing_session.user_id)
            owner_name = owner.nombre if owner else "Otro Usuario"
            return False, f"El puerto {port} ya está siendo utilizado por {owner_name}. Espera a que termine."

        # 2. Gestión Agresiva: Si el puerto está ocupado (por nosotros o por sistema externo)
        if IperfService.port_is_listening(port):
            try:
                # Si nosotros somos el dueño, o es un proceso huérfano, limpiamos
                subprocess.run(["fuser", "-k", "-n", "tcp", str(port)], capture_output=True)
                subprocess.run(["pkill", "-9", "iperf3"], capture_output=True)
                # Si había una sesión DB de este usuario, la marcamos como abortada antes de crear la nueva
                if existing_session:
                    existing_session.status = 'aborted'
                    existing_session.ended_at = datetime.utcnow()
                    db.session.commit()
                
                # Esperar a que el puerto se libere
                for _ in range(8):
                    time.sleep(0.25)
                    if not IperfService.port_is_listening(port):
                        break
            except Exception as e:
                print(f"Error en limpieza agresiva: {e}")

        # 3. Verificar si el puerto sigue ocupado tras limpieza
        if IperfService.port_is_listening(port):
            return False, f"El puerto {port} sigue bloqueado a nivel de sistema. Intenta con otro puerto."

        try:
            # Sesión inicial de "ESCUCHA"
            new_session = IperfSession(
                mode='server', port=port, status='running', user_id=user_id,
                started_at=datetime.utcnow()
            )
            db.session.add(new_session)
            db.session.commit()
            session_id = new_session.id
            IperfService._live_data[session_id] = {"measurements": [], "summary": None, "logs": []}
            
            cmd = ["iperf3", "-s", "-p", str(port), "--forceflush"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
            with IperfService._lock:
                IperfService._active_procs[session_id] = proc
            
            threading.Thread(target=IperfService._iperf3_reader, args=(proc, "server", session_id, app, user_id), daemon=True).start()
            
            # 4. Esperar a que NUESTRO proceso active el puerto
            for _ in range(10):
                time.sleep(0.3)
                if proc.poll() is not None:
                    error_msg = "Error desconocido"
                    try:
                        error_msg = proc.stdout.readline().strip()
                    except: pass
                    return False, f"Error al arrancar iperf3: {error_msg}"
                
                if IperfService.port_is_listening(port):
                    return True, f"Servidor iniciado exitosamente en el puerto {port}."

            return False, f"Timeout: el servidor iperf3 no activó el puerto {port} a tiempo."
        except Exception as e:
            return False, f"Error fatal: {str(e)}"

    @staticmethod
    def stop_server(user_id):
        session = IperfSession.query.filter_by(user_id=user_id, status='running').order_by(IperfSession.id.desc()).first()
        if not session:
            return False, "No hay servidor activo para este usuario."
        
        session.status = 'aborted'
        session.ended_at = datetime.utcnow()
        db.session.commit()

        with IperfService._lock:
            proc = IperfService._active_procs.get(session.id)
            if proc:
                proc.terminate()
                return True, "Servidor detenido correctamente."
        
        return True, "Estado del servidor limpiado."

    @staticmethod
    def is_server_running(user_id=None):
        query = IperfSession.query.filter_by(status='running', mode='server')
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.count() > 0

    @staticmethod
    def run_test_async(test_id, app):
        thread = threading.Thread(target=IperfService._execute_client_test, args=(test_id, app))
        thread.start()

    @staticmethod
    def _execute_client_test(test_id, app):
        with app.app_context():
            test = IperfTest.query.get(test_id)
            if not test: return
            test.status = 'running'
            test.started_at = datetime.utcnow()
            db.session.commit()

            new_session = IperfSession(
                mode='client', host=test.target_host, port=test.port,
                protocol=test.protocol.lower(), duration_s=test.duration,
                status='running', user_id=test.user_id
            )
            db.session.add(new_session)
            db.session.commit()

            cmd = ["iperf3", "-c", test.target_host, "-p", str(test.port),
                   "-t", str(test.duration), "--forceflush", "-i", "1"]
            if test.protocol.lower() == 'udp':
                cmd += ["-u", "-b", "100M"]

            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                IperfService._iperf3_reader(proc, "client", new_session.id, app, test.user_id)
                test.status = 'completed'
                test.results_json = json.dumps({"session_id": new_session.id})
            except Exception as e:
                test.status = 'failed'
                test.error_message = str(e)
            test.finished_at = datetime.utcnow()
            db.session.commit()
