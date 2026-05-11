"""
callbacks.py — Lee el log de iperf3 directamente para graficar.
No depende de la DB para las métricas en tiempo real.
"""
import re
import os
import time
from dash import Output, Input, State, callback_context, no_update, html
from flask_login import current_user
from datetime import datetime
import traceback

from app.modules.iperf.services import IperfService
from app.modules.iperf.dashboard_v2.debug_logger import debug_logger
from app.modules.iperf.models import IperfSession
from app.modules.iperf.dashboard_v2.state import timestamps, recv_mbps, jitter_ms, retransmits, log_lines, lock as state_lock
import plotly.graph_objs as go

# Cache de sesión para evitar queries excesivas
_session_cache = {"last_query": 0, "session": None}

# ─── Ruta del log (misma que services.py) ─────────────────────────────────────
LOG_PATH = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"

# ─── Regex para parsear líneas de datos ───────────────────────────────────────
DATA_RE = re.compile(
    r'\[\s*(?P<id>\d+|SUM)\]\s+'
    r'(?P<t0>[\d.]+)-(?P<t1>[\d.]+)\s+sec\s+'
    r'[\d.]+\s+\w+Bytes\s+'
    r'(?P<rate>[\d.]+)\s+(?P<unit>[GkMK])bits/sec'
    r'(?:\s+(?P<jitter>[\d.]+)\s+ms)?'           # UDP Jitter (ej. 0.123 ms)
    r'(?:\s+(?P<lost>\d+)/\s*(?P<total>\d+))?'   # UDP Lost/Total (ej. 0/100)
    r'(?:\s+(?P<retx>\d+))?'                     # TCP Retransmits (ej. 42)
    r'.*?(?:\s+(?P<role>sender|receiver))?\s*$'
)
SEP_RE      = re.compile(r'^[\s\-]+$')
ACCEPTED_RE = re.compile(r'Accepted connection from')
LISTEN_RE   = re.compile(r'Server listening on')

MAX_POINTS = 30   # ventana deslizante de puntos visibles


def _to_gbps(rate, unit):
    u = unit.upper()
    return {"G": rate, "M": rate / 1000, "K": rate / 1_000_000}.get(u, rate / 1000)


# ─── Parser del log ────────────────────────────────────────────────────────────
def _parse_log(log_path=LOG_PATH, max_points=MAX_POINTS):
    """
    Lee el archivo de log de iperf3 y extrae las últimas `max_points`
    mediciones de la sesión activa más reciente.

    Retorna: (timestamps, y_bw, y_jitter, log_lines_raw, is_active)
    - timestamps : lista de strings HH:MM:SS o floats t1
    - y_bw       : lista de floats en Gbps
    - y_jitter   : lista de floats en ms
    - log_lines_raw : últimas 80 líneas crudas del log
    - is_active  : True si hay una sesión activa (no ha aparecido "Server listening" al final)
    """
    if not os.path.exists(log_path):
        return [], [], [], [], False

    try:
        # Optimización: Leer los últimos 512KB del archivo para asegurar encontrar el inicio de sesión
        with open(log_path, "rb") as f:
            fsize = os.path.getsize(log_path)
            read_size = 524288  # 512KB
            if fsize > read_size:
                f.seek(-read_size, os.SEEK_END)
            chunk = f.read().decode('utf-8', errors='ignore')
            lines = chunk.splitlines()
    except Exception as e:
        debug_logger.error(f"_parse_log error: {e}")
        return [], [], [], [], False

    raw_tail = [l.rstrip() for l in lines[-40:]]

    # Encontrar el inicio de la sesión más reciente
    # (última línea "Accepted connection from")
    session_start = 0
    for i in range(len(lines) - 1, -1, -1):
        if ACCEPTED_RE.search(lines[i]):
            session_start = i
            break

    session_lines = lines[session_start:]

    # Determinar si la sesión sigue activa
    # (si "Server listening on" aparece DESPUÉS del último "Accepted", ya terminó)
    is_active = True
    for l in session_lines[1:]:   # saltar el propio "Accepted" line
        if LISTEN_RE.search(l):
            is_active = False

    # Parsear mediciones — usar solo líneas [SUM] o la última línea individual
    # por intervalo de 1 segundo.
    # Agrupamos por intervalo t0-t1 y tomamos SUM si existe.
    intervals = {}   # key: (t0, t1) → data dict

    for line in session_lines:
        m = DATA_RE.search(line)
        if not m:
            continue

        t0   = float(m.group("t0"))
        t1   = float(m.group("t1"))
        dur  = round(t1 - t0, 2)
        sid  = m.group("id").strip()
        role = m.group("role") or ""

        # Ignorar líneas de resumen final (role = sender/receiver y dur > 1.5)
        if role and dur > 1.5:
            continue

        gbps   = _to_gbps(float(m.group("rate")), m.group("unit"))
        jitter = float(m.group("jitter")) if m.group("jitter") else 0.0
        
        # Retransmisiones (TCP) o Perdidos (UDP)
        retx   = int(m.group("retx") or m.group("lost") or 0)

        key = (round(t0, 1), round(t1, 1))
        item = {"gbps": gbps, "jitter": jitter, "retx": retx, "t1": t1}
        
        if sid == "SUM":
            item["is_sum"] = True
            intervals[key] = item
        elif key not in intervals or not intervals[key].get("is_sum"):
            item["is_sum"] = False
            intervals[key] = item

    # Ordenar por t1 y recortar a max_points
    sorted_data = sorted(intervals.values(), key=lambda d: d["t1"])
    sorted_data = sorted_data[-max_points:]

    # Usar formato HH:MM:SS como en el test funcional
    ts     = [datetime.now().strftime('%H:%M:%S')] * len(sorted_data) 
    # Wait, if I use the same time for all it will be a mess. 
    # Let's use relative seconds or fake timestamps for now to ensure they are unique strings.
    ts     = [datetime.fromtimestamp(time.time() - (len(sorted_data)-i)).strftime('%H:%M:%S') for i in range(len(sorted_data))]
    
    y_bw   = [d["gbps"]   for d in sorted_data]
    y_jit  = [d["jitter"] for d in sorted_data]
    y_retx = [d["retx"]   for d in sorted_data]

    return ts, y_bw, y_jit, y_retx, raw_tail, is_active


# ─── Figuras ──────────────────────────────────────────────────────────────────
def _empty_fig(label=""):
    fig = go.Figure()
    fig.update_layout(
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[dict(
            text=label, xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#64748b", size=12),
        )],
    )
    return fig


def _make_fig(x, y, color_rgb):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(x), y=list(y),
        mode="lines+markers",
        line=dict(color=f"rgb({color_rgb})", width=2, shape="spline"),
        fill="tozeroy",
        fillcolor=f"rgba({color_rgb}, 0.08)",
        marker=dict(size=4, color=f"rgb({color_rgb})"),
        hoverinfo="y+x",
    ))
    fig.update_layout(
        autosize=True,
        uirevision="lock",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=10, t=10, b=30),
        xaxis=dict(showgrid=False, color="#64748b", tickfont=dict(size=9), type='category', dtick=5),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="#64748b", zeroline=False, tickfont=dict(size=9)),
        hovermode="closest",
    )
    return fig


def _make_bar_fig(x, y, color_hex):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(x), y=list(y),
        marker_color=color_hex,
        opacity=0.8,
    ))
    fig.update_layout(
        autosize=True,
        uirevision="lock",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=10, t=10, b=30),
        xaxis=dict(showgrid=False, color="#64748b", tickfont=dict(size=9), type='category', dtick=5),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="#64748b", zeroline=False, tickfont=dict(size=9)),
    )
    return fig


def register_callbacks(dash_app, lock, timestamps, recv_mbps, jitter_ms, retransmits, log_lines, empty_graph):

    # ─── NAVEGACIÓN SPA ───────────────────────────────────────────────────────
    @dash_app.callback(
        [Output("panel-server",  "className"),
         Output("panel-client",  "className"),
         Output("panel-history", "className")],
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def switch_tabs(pathname):
        try:
            ON  = "flex-1 min-h-0 flex flex-col animate-in fade-in duration-500 overflow-hidden"
            OFF = "hidden"
            path = (pathname or "").rstrip("/")
            if path in ("/iperf/server", "/iperf", ""):
                return ON, OFF, OFF
            if path == "/iperf/client":
                return OFF, ON, OFF
            if path == "/iperf/history":
                return OFF, OFF, ON
            return ON, OFF, OFF
        except Exception as e:
            debug_logger.error(f"switch_tabs: {e}\n{traceback.format_exc()}")
            return no_update, no_update, no_update

    # ─── CONTROL SERVIDOR ─────────────────────────────────────────────────────
    @dash_app.callback(
        [Output("srv-status-label", "children"),
         Output("srv-status-label", "className"),
         Output("srv-status-dot",   "className"),
         Output("srv-status-card",  "className")],
        [Input("btn-srv-start", "n_clicks"),
         Input("btn-srv-stop",  "n_clicks")],
        State("srv-port", "value"),
        prevent_initial_call=True,
    )
    def control_server(n_start, n_stop, srv_port):
        try:
            ctx = callback_context
            if not ctx.triggered:
                return (no_update,) * 4
            btn = ctx.triggered[0]["prop_id"].split(".")[0]
            port = srv_port or 5201

            if btn == "btn-srv-start":
                ok, msg = IperfService.start_server(current_user.id, port)
                if ok:
                    return (
                        "ACTIVO", "text-[10px] font-black uppercase tracking-widest text-emerald-500",
                        "w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]",
                        "flex items-center gap-3 px-4 py-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5",
                    )
                return (
                    "OCUPADO", "text-[10px] font-black uppercase tracking-widest text-amber-500",
                    "w-2 h-2 rounded-full bg-amber-500",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-amber-500/30 bg-amber-500/5",
                )

            if btn == "btn-srv-stop":
                IperfService.stop_server(current_user.id)
                return (
                    "STANDBY", "text-[10px] font-black uppercase tracking-widest text-label/40",
                    "w-2 h-2 rounded-full bg-slate-500",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-white/5 bg-white/5",
                )
        except Exception as e:
            debug_logger.error(f"control_server: {e}\n{traceback.format_exc()}")
        return (no_update,) * 4

    @dash_app.callback(
        [Output("bw-chart",            "figure"),
         Output("jitter-chart",        "figure"),
         Output("retx-chart",          "figure"),
         Output("current-bw",          "children"),
         Output("stat-jitter",         "children"),
         Output("stat-retx",           "children"),
         Output("stat-samples",        "children"),
         Output("current-bw-chart",    "children"),
         Output("stat-jitter-chart",   "children"),
         Output("stat-retx-chart",     "children"),
         Output("log-container",       "children"),
         Output("last-update",         "children"),
         Output("modal-summary",       "className"),
         Output("modal-msg",           "children"),
         Output("modal-download-link", "href")],
        Input("interval-update", "n_intervals"),
        State("ui-state", "data"),
        prevent_initial_call=False,
    )
    def update_server(n, ui_state):
        try:
            if not current_user.is_authenticated:
                return (_empty_fig("LOGIN"), _empty_fig("LOGIN"), _empty_fig("LOGIN"),
                        "0.00", "0.000", "0", "0", "0.00", "0.000", "0",
                        "", datetime.now().strftime('%H:%M:%S'),
                        "hidden", "", "#")

            # 1. Obtener Datos del Estado Global (1:1 con test/app.py)
            with state_lock:
                ts   = list(timestamps)
                y_bw_mbps = list(recv_mbps)
                y_jit  = list(jitter_ms)
                y_retx = list(retransmits)
                raw_lines = list(log_lines)
            
            # Convertir Mbps a Gbps para el label (Nexus Style)
            y_bw_gbps = [round(v / 1000, 4) for v in y_bw_mbps]

            # Link de reporte (Cache)
            now = time.time()
            if now - _session_cache["last_query"] > 5:
                s = IperfSession.query.filter_by(user_id=current_user.id, mode="server").order_by(IperfSession.id.desc()).first()
                if s: _session_cache["session"] = s
                _session_cache["last_query"] = now
            
            s = _session_cache["session"]
            report_url = f"/iperf/report/{s.id}" if s else "#"

            # 2. Logs
            log_text = "\n".join(raw_lines) if raw_lines else "[NEXUS] Esperando transmisión..."
            log_el = html.Pre(log_text, id="log-output", className="text-emerald-500/60 leading-relaxed whitespace-pre-wrap")

            # 3. Validar datos
            if not y_bw_gbps:
                fig_label = "ESCUCHANDO..." if IperfService.is_server_running(current_user.id) else "SIN SEÑAL"
                return (_empty_fig(fig_label), _empty_fig("STANDBY"), _empty_fig("STANDBY"),
                        "0.00", "0.000", "0", "0", "0.00", "0.000", "0",
                        log_el, datetime.now().strftime('%H:%M:%S'),
                        "hidden", "", report_url)

            # 4. Graficar
            bw_fig     = _make_fig(ts, y_bw_gbps,  "0, 212, 255")
            jitter_fig = _make_fig(ts, y_jit, "255, 209, 102")
            retx_fig   = _make_bar_fig(ts, y_retx, "#ff6b6b")
            
            cur_bw     = f"{y_bw_gbps[-1]:.2f}"
            cur_jit    = f"{y_jit[-1]:.3f}"
            cur_retx   = str(y_retx[-1])
            total_retx = str(sum(y_retx))
            samples    = str(len(y_bw_gbps))

            return (bw_fig, jitter_fig, retx_fig,
                    cur_bw, cur_jit, total_retx, samples,
                    cur_bw, cur_jit, cur_retx,
                    log_el, datetime.now().strftime('%H:%M:%S'),
                    "hidden", "", report_url)

        except Exception as e:
            debug_logger.error(f"update_server: {e}\n{traceback.format_exc()}")
            return (no_update,) * 15

        except Exception as e:
            debug_logger.error(f"update_server: {e}\n{traceback.format_exc()}")
            return (no_update,) * 15

        except Exception as e:
            debug_logger.error(f"update_server: {e}\n{traceback.format_exc()}")
            return (no_update,) * 15

    # ─── CONTROL CLIENTE ──────────────────────────────────────────────────────
    @dash_app.callback(
        [Output("cli-status-label", "children"),
         Output("cli-status-label", "className"),
         Output("cli-status-card",  "className")],
        Input("btn-cli-start", "n_clicks"),
        [State("cli-host",     "value"),
         State("cli-port",     "value"),
         State("cli-duration", "value"),
         State("cli-parallel", "value"),
         State("cli-bitrate",  "value"),
         State("cli-proto",    "value")],
        prevent_initial_call=True,
    )
    def control_client(n_clicks, host, port, duration, parallel, bitrate, proto):
        try:
            if not n_clicks:
                return (no_update,) * 4
            from flask import current_app
            from app.modules.iperf.models import IperfSession
            import subprocess, threading
            app = current_app._get_current_object()

            new_s = IperfSession(
                mode="client", host=host, port=port,
                protocol=proto or "tcp", duration_s=duration,
                parallel=parallel or 1,
                status="running", user_id=current_user.id,
                started_at=datetime.utcnow(),
            )
            from app import db
            db.session.add(new_s)
            db.session.commit()
            sid = new_s.id
            IperfService._live_data[sid] = {"measurements": [], "summary": None, "logs": []}

            cmd = ["iperf3", "-c", host, "-p", str(port or 5201),
                   "-t", str(duration or 10), "-P", str(parallel or 1), 
                   "--forceflush", "-i", "1"]
            
            if bitrate:
                cmd += ["-b", str(bitrate)]
            
            if (proto or "tcp") == "udp":
                cmd += ["-u"]
                if not bitrate:
                    cmd += ["-b", "10M"] # Default UDP bitrate if not specified

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True, bufsize=1)
            IperfService._active_procs[sid] = proc
            threading.Thread(
                target=IperfService._iperf3_reader,
                args=(proc, "client", sid, app, current_user.id),
                daemon=True,
            ).start()

            return ("CORRIENDO", "text-[10px] font-black uppercase tracking-widest text-emerald-500",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5")
        except Exception as e:
            debug_logger.error(f"control_client: {e}\n{traceback.format_exc()}")
            return (no_update,) * 3

    # ─── MÉTRICAS CLIENTE — lee desde _live_data (el cliente no tiene log file) ─
    @dash_app.callback(
        [Output("cli-bw-chart",          "figure"),
         Output("cli-jitter-chart",      "figure"),
         Output("cli-current-bw",        "children"),
         Output("cli-stat-jitter",       "children"),
         Output("cli-current-bw-chart",  "children"),
         Output("cli-stat-jitter-chart", "children"),
         Output("cli-log-container",     "children"),
         Output("cli-last-update",       "children"),
         Output("cli-realtime-sub",      "children")],
        Input("interval-update", "n_intervals"),
        prevent_initial_call=False,
    )
    def update_client(n):
        try:
            if not current_user.is_authenticated:
                return (_empty_fig("LOGIN"), _empty_fig("LOGIN"),
                        "0.00", "0.000", "0.00", "0.000",
                        "", datetime.now().strftime('%H:%M:%S'), "ACCESO RESTRINGIDO")

            # Buscar sesión de cliente más reciente con datos en _live_data
            from app.modules.iperf.models import IperfSession
            db_sessions = (
                IperfSession.query
                .filter_by(user_id=current_user.id, mode="client")
                .order_by(IperfSession.id.desc())
                .limit(10)
                .all()
            )

            session = None
            live    = None
            for s in db_sessions:
                d = IperfService._live_data.get(s.id)
                if d and d.get("measurements"):
                    session = s
                    live    = d
                    break

            no_data_log = html.Pre(
                "[NEXUS] Esperando test de cliente...",
                id="cli-log-output",
                className="text-emerald-500/60 leading-relaxed whitespace-pre-wrap",
            )

            if not live or not live.get("measurements"):
                return (_empty_fig("SIN SEÑAL"), _empty_fig("STANDBY"),
                        "0.00", "0.000", "0.00", "0.000",
                        no_data_log, datetime.now().strftime('%H:%M:%S'),
                        "ESPERANDO ACTIVACIÓN DEL MOTOR")

            meas     = live["measurements"][-MAX_POINTS:]
            x        = [m.get("ts", str(m.get("t1", i))) for i, m in enumerate(meas)]
            y_bw     = [float(m.get("gbps",   0)) for m in meas]
            y_jitter = [float(m.get("jitter", 0)) for m in meas]

            bw_fig     = _make_fig(x, y_bw,     "37, 99, 235")
            jitter_fig = _make_fig(x, y_jitter, "245, 158, 11")
            cur_bw     = f"{y_bw[-1]:.2f}"
            cur_jit    = f"{y_jitter[-1]:.3f}"

            logs = "\n".join(live.get("logs", [])[-100:])
            log_el = html.Pre(
                logs or "[NEXUS] Esperando telemetría...",
                id="cli-log-output",
                className="text-emerald-500/60 leading-relaxed whitespace-pre-wrap",
            )
            sub = (f"TRANSMISIÓN ACTIVA"
                   f" — {session.host if session else 'LOCALHOST'}"
                   f" · {len(meas)} MUESTRAS")

            return (bw_fig, jitter_fig,
                    cur_bw, cur_jit, cur_bw, cur_jit,
                    log_el, datetime.now().strftime('%H:%M:%S'), sub)

        except Exception as e:
            debug_logger.error(f"update_client: {e}\n{traceback.format_exc()}")
            return (no_update,) * 9

    # ─── MODAL ────────────────────────────────────────────────────────────────
    @dash_app.callback(
        Output("ui-state", "data", allow_duplicate=True),
        [Input("btn-modal-close", "n_clicks"),
         Input("btn-save-db",     "n_clicks")],
        State("ui-state", "data"),
        prevent_initial_call=True,
    )
    def handle_modal(n_close, n_save, ui_state):
        try:
            ctx = callback_context
            if not ctx.triggered:
                return ui_state
            btn = ctx.triggered[0]["prop_id"].split(".")[0]

            from app.modules.iperf.models import IperfSession, IperfMeasurement, IperfSessionSummary
            from app import db

            # Buscar sesión con summary en memoria
            session = None
            live    = None
            for sid, d in sorted(IperfService._live_data.items(), reverse=True):
                if d and d.get("summary"):
                    session = IperfSession.query.get(sid)
                    live    = d
                    break

            if not session:
                return ui_state

            if btn == "btn-save-db" and live.get("measurements"):
                for m in live["measurements"]:
                    db.session.add(IperfMeasurement(
                        session_id=session.id,
                        gbps=m.get("gbps", 0),
                        jitter_ms=m.get("jitter", 0),
                        retransmits=m.get("retx", 0),
                    ))
                sv = live["summary"]
                db.session.add(IperfSessionSummary(
                    session_id=session.id,
                    avg_gbps=sv.get("avg_gbps", 0),
                    max_gbps=sv.get("max_gbps", 0),
                    min_gbps=sv.get("min_gbps", 0),
                    avg_jitter_ms=sv.get("avg_jitter_ms", 0),
                    total_retransmits=sv.get("total_retransmits", 0),
                    total_samples=sv.get("total_samples", 0),
                ))
                session.status = "completed"
                db.session.commit()

            IperfService._live_data[session.id]["summary"] = None
            return ui_state
        except Exception as e:
            debug_logger.error(f"handle_modal: {e}\n{traceback.format_exc()}")
            return ui_state

    # ─── HISTORIAL ────────────────────────────────────────────────────────────
    @dash_app.callback(
        Output("history-list", "children"),
        [Input("btn-history-refresh", "n_clicks"),
         Input("url", "pathname")],
        prevent_initial_call=False,
    )
    def update_history(n, pathname):
        try:
            from app.modules.iperf.models import IperfSession
            if not current_user.is_authenticated:
                return [html.Tr([html.Td("Usuario no autenticado", colSpan=7,
                                         className="py-10 text-center text-label/20 font-black italic")])]

            sessions = (IperfSession.query
                        .filter_by(user_id=current_user.id)
                        .order_by(IperfSession.id.desc())
                        .limit(50).all())

            if not sessions:
                return [html.Tr([html.Td("No hay registros disponibles", colSpan=7,
                                          className="py-10 text-center text-label/20 font-black italic")])]

            rows = []
            for s in sessions:
                mode_color  = ("text-emerald-500 bg-emerald-500/10" if s.mode == "server"
                               else "text-primary bg-primary/10")
                proto_color = ("text-amber-500 bg-amber-500/10" if s.protocol == "udp"
                               else "text-sky-500 bg-sky-500/10")
                # FIX: s.summary puede ser None
                bw = (
                    f"{s.summary.avg_gbps:.2f} Gbps"
                    if s.summary and s.summary.avg_gbps is not None
                    else ("EN CURSO..." if s.status == "running" else "--")
                )
                rows.append(html.Tr(className="hover:bg-white/5 transition-colors", children=[
                    html.Td(f"#{s.id}", className="py-4 px-6 text-xs font-black text-label/40"),
                    html.Td(html.Span(s.mode.upper(),
                                     className=f"px-3 py-1 rounded-lg text-[10px] font-black tracking-widest {mode_color}"),
                            className="py-4 px-4 text-center"),
                    html.Td(html.Span(s.protocol.upper(),
                                     className=f"px-3 py-1 rounded-lg text-[10px] font-black tracking-widest {proto_color}"),
                            className="py-4 px-4 text-center"),
                    html.Td(s.host or "LOCALHOST",
                            className="py-4 px-4 text-xs font-bold text-text truncate"),
                    html.Td(bw, className="py-4 px-4 text-center text-xs font-black text-emerald-500"),
                    html.Td(s.started_at.strftime("%d/%m/%Y %H:%M") if s.started_at else "--",
                            className="py-4 px-4 text-center text-[10px] font-bold text-label/40"),
                    html.Td(html.A(html.I(className="fas fa-file-pdf"),
                                   href=f"/iperf/report/{s.id}", target="_blank",
                                   className="text-primary/40 hover:text-primary transition-all p-2"),
                            className="py-4 px-6 text-right"),
                ]))
            return rows
        except Exception as e:
            debug_logger.error(f"update_history: {e}\n{traceback.format_exc()}")
            return [html.Tr([html.Td(f"Error: {e}", colSpan=7,
                                     className="py-10 text-center text-rose-500 font-black italic")])]
