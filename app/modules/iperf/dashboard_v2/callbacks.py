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
from app.modules.iperf.dashboard_v2.state import timestamps, recv_mbps, jitter_ms, retransmits, log_lines, lock as state_lock, clear_buffers
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


def _make_empty_log(msg="ESPERANDO TRANSMISIÓN..."):
    return html.Div(className="flex flex-col items-center justify-center h-full py-20 select-none", children=[
        html.I(className="fas fa-terminal text-8xl mb-8 text-primary/30"),
        html.P(msg, className="text-[11px] font-black tracking-[0.5em] uppercase text-center text-slate-100")
    ])


# ─── Figuras ──────────────────────────────────────────────────────────────────
def _empty_fig(label=""):
    fig = go.Figure()
    
    # Configuración de estilo premium sólido
    # NOTE: Plotly no soporta CSS vars — estos hex mapean a tokens:
    #   #64748b = --color-secondary (Slate-500)
    #   #2563eb = --color-primary (Blue-600)
    #   #94a3b8 = Slate-400 (muted text)
    color = "#64748b"  # → --color-secondary
    icon = "📊"
    subtext = "EL SISTEMA ESTÁ LISTO PARA RECIBIR DATOS"
    
    if "ESCUCHANDO" in label:
        icon = "📡"
        color = "#2563eb"  # → --color-primary
        subtext = "PUERTO ABIERTO • ESPERANDO TRANSMISIÓN..."
    elif "STANDBY" in label or "SIN SEÑAL" in label:
        icon = "💤"
        subtext = "SISTEMA EN REPOSO • LISTO PARA MONITOREAR"
    elif "LOGIN" in label:
        icon = "🔒"
        subtext = "AUTENTICACIÓN REQUERIDA"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        margin=dict(t=0, b=0, l=0, r=0),
        annotations=[
            # Icono Central Grande
            dict(
                text=icon,
                xref="paper", yref="paper",
                x=0.5, y=0.6,
                showarrow=False,
                font=dict(size=50),
            ),
            # Título principal (Label)
            dict(
                text=label.upper(),
                xref="paper", yref="paper",
                x=0.5, y=0.42,
                showarrow=False,
                font=dict(family="Outfit, sans-serif", size=15, color=color, weight=900),
            ),
            # Subtexto Premium Descriptivo
            dict(
                text=subtext,
                xref="paper", yref="paper",
                x=0.5, y=0.32,
                showarrow=False,
                font=dict(family="Outfit, sans-serif", size=10, color="#94a3b8", weight=600),  # → Slate-400 muted
            )
        ],
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


def _make_event_toast(title, msg, type="info", ts=None):
    if ts is None: ts = time.time()
    # Mapeo de tipos a variables CSS del Nexus Framework
    css_var_map = {
        "success": "success",
        "error":   "danger",
        "warning": "warning",
        "info":    "primary"
    }
    v = css_var_map.get(type, "primary")
    
    icon_map = {
        "success": "fa-check-double",
        "error":   "fa-circle-xmark",
        "warning": "fa-triangle-exclamation",
        "info":    "fa-circle-info"
    }
    icon = icon_map.get(type, "fa-circle-info")
    
    return html.Div(id={"type": "event-toast", "ts": ts}, className="group relative overflow-hidden bg-surface-container/90 backdrop-blur-3xl border border-white/5 rounded-panel p-6 shadow-[0_30px_70px_rgba(0,0,0,0.6)] flex items-center gap-6 animate-in slide-in-from-right duration-700 w-[360px] hover:scale-[1.03] transition-all cursor-pointer", children=[
        
        # Aura de color dinámica (Premium Glow)
        html.Div(className="absolute -right-16 -top-16 w-48 h-48 blur-[80px] rounded-full transition-all duration-1000 group-hover:blur-[100px]", 
                 style={"backgroundColor": f"rgba(var(--color-{v}), 0.25)"}),
        
        # Icono con Glassmorphism y Elevación
        html.Div(className="relative w-20 h-20 rounded-panel flex items-center justify-center flex-shrink-0 border shadow-[inset_0_2px_4px_rgba(255,255,255,0.1)] transition-transform duration-500 group-hover:rotate-6", 
                 style={
                     "background": f"linear-gradient(135deg, rgba(var(--color-{v}), 0.3), rgba(var(--color-{v}), 0.05))",
                     "borderColor": f"rgba(var(--color-{v}), 0.3)"
                 },
                 children=[
                    html.I(className=f"fas {icon} text-3xl", 
                           style={"color": f"rgb(var(--color-{v}))", "filter": f"drop-shadow(0 0 12px rgba(var(--color-{v}), 0.6))"})
                 ]),
        
        # Cuerpo de Texto
        html.Div(className="relative flex-1", children=[
            html.Div(className="flex items-center justify-between mb-2.5", children=[
                html.P(title, className="text-[11px] font-black uppercase tracking-[0.3em] italic leading-none", 
                       style={"color": f"rgb(var(--color-{v}))"}),
                # Indicador de Pulso Neón
                html.Div(className="w-2 h-2 rounded-full animate-pulse", 
                         style={"backgroundColor": f"rgb(var(--color-{v}))", "boxShadow": f"0 0 10px rgb(var(--color-{v}))"})
            ]),
            html.P(msg, className="text-[15px] font-extrabold text-label leading-snug tracking-tight mb-1"),
            html.P("HACE UN MOMENTO", className="text-[9px] font-black text-label/20 tracking-widest")
        ]),

        # Barra de tiempo premium (Progress bar)
        html.Div(className="absolute bottom-0 left-0 h-1 w-full", 
                 style={"backgroundColor": f"rgba(var(--color-{v}), 0.1)"},
                 children=[
                    html.Div(className="h-full animate-out fade-out duration-[5000ms] ease-linear", 
                             style={"width": "100%", "backgroundColor": f"rgb(var(--color-{v}))"})
                 ])
    ])


def register_callbacks(dash_app, lock, timestamps, recv_mbps, jitter_ms, retransmits, log_lines, empty_graph):
    
    def find_available_port():
        """Busca el primer puerto libre en el rango 5201-5210."""
        from app.modules.iperf.models import IperfSession
        for p in range(5201, 5211):
            # 1. Validar a nivel de Socket (Sistema)
            if not IperfService.port_is_listening(p):
                # 2. Validar a nivel de DB (Nuestra App)
                existing = IperfSession.query.filter_by(status='running', port=p, mode='server').first()
                if not existing:
                    return p
        return None

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
            if path in ("/iperf/live", "/iperf/live/server"):
                return ON, OFF, OFF
            if path == "/iperf/live/client":
                return OFF, ON, OFF
            return ON, OFF, OFF
        except Exception as e:
            debug_logger.error(f"switch_tabs: {e}\n{traceback.format_exc()}")
            return no_update, no_update, no_update

    # ─── CONTROL SERVIDOR ─────────────────────────────────────────────────────
    @dash_app.callback(
        [Output("srv-status-label", "children"),
         Output("srv-status-label", "className"),
         Output("srv-status-dot",   "className"),
         Output("srv-status-card",  "className"),
         Output("srv-toggle-text",  "children"),
         Output("srv-toggle-icon",  "className"),
         Output("btn-srv-toggle",   "className"),
         Output("toast-trigger",    "data"),
         Output("modal-busy",       "className"),
         Output("modal-busy-msg",   "children"),
         Output("modal-busy-suggested", "children")],
        Input("btn-srv-toggle", "n_clicks"),
        State("srv-port", "value"),
        prevent_initial_call=True,
    )
    def toggle_server(n, port):
        if not n: return (no_update,) * 11
        try:
            if not IperfService.is_server_running(current_user.id):
                success, msg = IperfService.start_server(current_user.id, port=port)
                
                if not success and "utilizado por" in msg:
                    suggested = find_available_port()
                    return (no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update,
                            "modal-nexus-active fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md",
                            msg, str(suggested if suggested else "5201"))

                toast = {"title": "SERVIDOR IPERF3", "msg": msg, "type": "success" if success else "error", "ts": time.time()}
                return (
                    "ONLINE" if success else "ERROR", 
                    "text-[10px] font-black uppercase tracking-widest text-primary" if success else "text-[10px] font-black uppercase tracking-widest text-rose-500",
                    "w-2 h-2 rounded-full bg-primary animate-pulse" if success else "w-2 h-2 rounded-full bg-rose-500",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-primary/20 bg-primary/10 shadow-[0_0_20px_rgba(37,99,235,0.2)]" if success else "flex items-center gap-3 px-4 py-2 rounded-xl border border-rose-500/20 bg-rose-500/10",
                    "DETENER" if success else "REINTENTAR", 
                    "fas fa-stop mr-2" if success else "fas fa-sync mr-2",
                    "bg-rose-500 text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all flex items-center" if success else "bg-primary text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all flex items-center",
                    toast,
                    "hidden", "", ""
                )
            else:
                IperfService.stop_server(current_user.id)
                toast = {"title": "SERVIDOR IPERF3", "msg": "Servidor detenido manualmente.", "type": "info", "ts": time.time()}
                return (
                    "STANDBY", "text-[10px] font-black uppercase tracking-widest text-label/40",
                    "w-2 h-2 rounded-full bg-slate-500",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-white/5 bg-white/5",
                    "INICIAR", "fas fa-play mr-2",
                    "bg-primary text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all flex items-center",
                    toast,
                    "hidden", "", ""
                )
        except Exception as e:
            debug_logger.error(f"toggle_server: {e}\n{traceback.format_exc()}")
            return (no_update,) * 11

    @dash_app.callback(
        Output("modal-busy", "className", allow_duplicate=True),
        Input("btn-modal-busy-close", "n_clicks"),
        prevent_initial_call=True
    )
    def close_busy_modal(n):
        return "hidden"

    @dash_app.callback(
        [Output("bw-chart",            "figure"),
         Output("jitter-chart",        "figure"),
         Output("current-bw-chart",    "children"),
         Output("stat-jitter-chart",   "children"),
         Output("log-container",       "children"),
         Output("last-update",         "children"),
         Output("modal-summary",       "className"),
         Output("modal-msg",           "children"),
         Output("modal-download-link", "href"),
         Output("toast-trigger",       "data", allow_duplicate=True)],
        Input("interval-update", "n_intervals"),
        State("ui-state", "data"),
        prevent_initial_call=True,
    )
    def update_server(n, ui_state):
        try:
            if not current_user.is_authenticated:
                return (_empty_fig("LOGIN"), _empty_fig("LOGIN"),
                        "0.00", "0.000",
                        "", datetime.now().strftime('%H:%M:%S'),
                        "hidden", "", "#", no_update)

            # 1. Buscar sesión de servidor activa para este usuario
            from app.modules.iperf.models import IperfSession
            s = IperfSession.query.filter_by(user_id=current_user.id, mode="server", status='running').order_by(IperfSession.id.desc()).first()
            
            # Si no hay una corriendo, buscamos la más reciente terminada para mostrar el modal si es necesario
            if not s:
                s = IperfSession.query.filter_by(user_id=current_user.id, mode="server").order_by(IperfSession.id.desc()).first()

            live = IperfService._live_data.get(s.id) if s else None
            
            if not live or not live.get("measurements"):
                # Si no hay datos live, verificamos si hay que mostrar el modal de una sesión recién terminada
                modal_class = "hidden"
                modal_msg = ""
                toast_data = no_update
                
                with state_lock:
                    if live and live.get("summary"):
                        summary_data = live.pop("summary")
                        modal_class = "modal-nexus-active fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md"
                        modal_msg = f"Prueba finalizada con éxito. Host: {s.host or 'Local'}"
                        IperfService._notified_sessions.add(s.id)
                        IperfService.stop_server(current_user.id)
                        IperfService.clear_buffers(current_user.id)

                fig_label = "ESCUCHANDO..." if IperfService.is_server_running(current_user.id) else "SIN SEÑAL"
                return (_empty_fig(fig_label), _empty_fig(fig_label),
                        "0.00", "0.000",
                        _make_empty_log(), datetime.now().strftime('%H:%M:%S'),
                        modal_class, modal_msg, f"/iperf/report/{s.id}" if s else "#", toast_data)

            # 2. Extraer datos de la sesión aislada
            with state_lock:
                meas = live["measurements"][-MAX_POINTS:]
                ts = [m.get("ts", "") for m in meas]
                y_bw_gbps = [m.get("gbps", 0) for m in meas]
                y_jit = [m.get("jitter", 0) for m in meas]
                raw_lines = live.get("logs", [])[-100:]

            # 3. Validar estado de finalización (NUEVA LÓGICA BASADA EN LIVE DATA)
            modal_class = "hidden"
            modal_msg = ""
            toast_data = no_update

            # Solo mostramos el modal si detectamos un resumen RECIÉN generado en memoria (Rule #10)
            with state_lock:
                live = IperfService._live_data.get(s.id) if s else None
                if live and live.get("summary"):
                    # Consumir el resumen para que no se repita el modal
                    summary_data = live.pop("summary") 
                    modal_class = "modal-nexus-active fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md"
                    modal_msg = f"Prueba finalizada con éxito. Host: {s.host or 'Local'}"
                    
                    # Log de auditoría de fin de prueba
                    IperfService._notified_sessions.add(s.id)
                    
                    # LIMPIEZA AGRESIVA POST-TEST (Rule #10)
                    IperfService.stop_server(current_user.id)
                    IperfService.clear_buffers(current_user.id)
                    
                    # Forzamos vaciado de variables locales para el return de este frame
                    y_bw_gbps = []
                    y_jit = []
                    raw_lines = ["[NEXUS] Sesión finalizada. Resultados guardados."]

                # Si el proceso fue abortado (cancelado por el usuario), s.status será 'aborted'
                elif s and s.status == 'aborted' and s.id not in IperfService._notified_sessions:
                    IperfService._notified_sessions.add(s.id)
                    toast_data = {"title": "TEST INTERRUMPIDO", "msg": "El proceso fue cancelado o se perdió la conexión.", "type": "warning", "ts": time.time()}
                    IperfService.stop_server(current_user.id)

            # 4. Logs
            log_text = "\n".join(raw_lines)
            log_el = html.Pre(log_text, id="log-output", className="text-emerald-400 leading-relaxed whitespace-pre-wrap") if raw_lines else _make_empty_log()

            # 5. Validar datos
            if not y_bw_gbps:
                fig_label = "ESCUCHANDO..." if IperfService.is_server_running(current_user.id) else "SIN SEÑAL"
                return (_empty_fig(fig_label), _empty_fig(fig_label),
                        "0.00", "0.000",
                        log_el, datetime.now().strftime('%H:%M:%S'),
                        modal_class, modal_msg, report_url, toast_data)

            # 6. Graficar
            bw_fig     = _make_fig(ts, y_bw_gbps,  "0, 212, 255")
            jitter_fig = _make_fig(ts, y_jit, "255, 209, 102")
            
            cur_bw     = f"{y_bw_gbps[-1]:.2f}"
            cur_jit    = f"{y_jit[-1]:.3f}"

            return (bw_fig, jitter_fig,
                    cur_bw, cur_jit,
                    log_el, datetime.now().strftime('%H:%M:%S'),
                    modal_class, modal_msg, f"/iperf/report/{s.id}" if s else "#", toast_data)

        except Exception as e:
            debug_logger.error(f"update_server: {e}\n{traceback.format_exc()}")
            return (no_update,) * 10

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
    @dash_app.callback(
        [Output("cli-status-label", "children"),
         Output("cli-status-label", "className"),
         Output("cli-status-card",  "className"),
         Output("cli-toggle-text",  "children"),
         Output("cli-toggle-icon",  "className"),
         Output("btn-cli-toggle",   "className"),
         Output("toast-trigger",    "data", allow_duplicate=True)],
        Input("btn-cli-toggle", "n_clicks"),
        [State("cli-host",      "value"),
         State("cli-port",      "value"),
         State("cli-duration",  "value"),
         State("cli-parallel",  "value"),
         State("cli-bitrate",   "value"),
         State("cli-proto",     "value"),
         State("cli-toggle-text", "children")],
        prevent_initial_call=True,
    )
    def toggle_client(n_clicks, host, port, duration, parallel, bitrate, proto, current_text):
        try:
            if not n_clicks: return (no_update,) * 7
            
            if current_text == "EJECUTAR TEST":
                clear_buffers()
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
                        cmd += ["-b", "10M"]

                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        universal_newlines=True, bufsize=1)
                IperfService._active_procs[sid] = proc
                threading.Thread(
                    target=IperfService._iperf3_reader,
                    args=(proc, "client", sid, app, current_user.id),
                    daemon=True,
                ).start()

                toast = {"title": "CLIENTE IPERF3", "msg": f"Iniciando test hacia {host}...", "type": "success", "ts": time.time()}
                return (
                    "CORRIENDO", "text-[10px] font-black uppercase tracking-widest text-emerald-500",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5",
                    "DETENER", "fas fa-stop mr-2",
                    "bg-rose-500 text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all flex items-center",
                    toast
                )
            else:
                # Detener procesos activos
                for sid in list(IperfService._active_procs.keys()):
                    proc = IperfService._active_procs.get(sid)
                    if proc:
                        try: proc.terminate()
                        except: pass
                
                toast = {"title": "CLIENTE IPERF3", "msg": "Test de cliente abortado.", "type": "warning", "ts": time.time()}
                return (
                    "IDLE", "text-[10px] font-black uppercase tracking-widest text-slate-400",
                    "flex items-center gap-3 px-4 py-2 rounded-xl border border-white/5 bg-white/5",
                    "EJECUTAR TEST", "fas fa-satellite-dish mr-2",
                    "bg-primary text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all flex items-center",
                    toast
                )
        except Exception as e:
            debug_logger.error(f"toggle_client: {e}\n{traceback.format_exc()}")
            return (no_update,) * 7

    # ─── MÉTRICAS CLIENTE — lee desde _live_data (el cliente no tiene log file) ─
    @dash_app.callback(
        [Output("cli-bw-chart",          "figure"),
         Output("cli-jitter-chart",      "figure"),
         Output("cli-current-bw-chart",  "children"),
         Output("cli-stat-jitter-chart", "children"),
         Output("cli-log-container",     "children"),
         Output("cli-last-update",       "children"),
         Output("modal-summary",       "className", allow_duplicate=True),
         Output("modal-msg",           "children", allow_duplicate=True),
         Output("modal-download-link", "href", allow_duplicate=True),
         Output("toast-trigger",       "data", allow_duplicate=True)],
        Input("interval-update", "n_intervals"),
        prevent_initial_call=True,
    )
    def update_client(n):
        try:
            if not current_user.is_authenticated:
                return (_empty_fig("LOGIN"), _empty_fig("LOGIN"),
                        "0.00", "0.000",
                        "", datetime.now().strftime('%H:%M:%S'),
                        "hidden", "", "#", no_update)

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

            no_data_log = _make_empty_log("ESPERANDO TEST DE CLIENTE...")

            if not live or not live.get("measurements"):
                return (_empty_fig("SIN SEÑAL"), _empty_fig("STANDBY"),
                        "0.00", "0.000",
                        no_data_log, datetime.now().strftime('%H:%M:%S'),
                        "hidden", "", "#", no_update)

            meas     = live["measurements"][-MAX_POINTS:]
            x        = [m.get("ts", str(m.get("t1", i))) for i, m in enumerate(meas)]
            y_bw     = [float(m.get("gbps",   0)) for m in meas]
            y_jitter = [float(m.get("jitter", 0)) for m in meas]
            # 3. Finalización (NUEVA LÓGICA BASADA EN LIVE DATA)
            modal_class = "hidden"
            modal_msg = ""
            toast_data = no_update

            with state_lock:
                live_s = IperfService._live_data.get(session.id) if session else None
                if live_s and live_s.get("summary"):
                    # Consumir resumen
                    live_s.pop("summary")
                    modal_class = "modal-nexus-active fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md"
                    modal_msg = f"Prueba de cliente finalizada. Destino: {session.host}"
                    IperfService._notified_sessions.add(session.id)
                    
                    # LIMPIEZA AGRESIVA POST-TEST (Rule #10)
                    IperfService.clear_buffers(current_user.id)
                    
                    # Forzamos vaciado local
                    y_bw = []
                    y_jitter = []
                    live_s["logs"] = ["[NEXUS] Test de cliente completado."]
                elif session and session.status == 'aborted' and session.id not in IperfService._notified_sessions:
                    IperfService._notified_sessions.add(session.id)
                    toast_data = {"title": "TEST INTERRUMPIDO", "msg": "El test de cliente fue cancelado.", "type": "warning", "ts": time.time()}

            bw_fig     = _make_fig(x, y_bw,     "37, 99, 235")
            jitter_fig = _make_fig(x, y_jitter, "245, 158, 11")
            cur_bw     = f"{y_bw[-1]:.2f}"
            cur_jit    = f"{y_jitter[-1]:.3f}"

            logs = "\n".join(live.get("logs", [])[-100:])
            log_el = html.Pre(
                logs,
                id="cli-log-output",
                className="text-emerald-400 leading-relaxed whitespace-pre-wrap",
            ) if logs else _make_empty_log("TEST ACTIVO • CAPTURANDO LOGS...")
            
            report_url = f"/iperf/report/{session.id}"

            return (bw_fig, jitter_fig,
                    cur_bw, cur_jit,
                    log_el, datetime.now().strftime('%H:%M:%S'),
                    modal_class, modal_msg, report_url, toast_data)

        except Exception as e:
            debug_logger.error(f"update_client: {e}\n{traceback.format_exc()}")
            return (no_update,) * 10

    @dash_app.callback(
        [Output("cli-proto", "value"),
         Output("btn-proto-tcp", "className"),
         Output("btn-proto-udp", "className")],
        [Input("btn-proto-tcp", "n_clicks"),
         Input("btn-proto-udp", "n_clicks")],
        [State("cli-proto", "value")],
        prevent_initial_call=False
    )
    def update_proto_toggle(n_tcp, n_udp, current):
        ctx = callback_context
        if not ctx.triggered:
            # Initial state
            return current, "proto-toggle-btn active", "proto-toggle-btn"
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "btn-proto-tcp":
            return "tcp", "proto-toggle-btn active", "proto-toggle-btn"
        else:
            return "udp", "proto-toggle-btn", "proto-toggle-btn active"


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

            query = IperfSession.query
            if current_user.role != 'administrador':
                query = query.filter_by(user_id=current_user.id)
                
            sessions = (query.order_by(IperfSession.id.desc())
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
    # ─── NOTIFICACIONES TOAST ──────────────────────────────────────────────────
    @dash_app.callback(
        Output("toast-container", "children"),
        [Input("toast-trigger",    "data"),
         Input("interval-update", "n_intervals")],
        State("toast-container", "children"),
        prevent_initial_call=True,
    )
    def trigger_notifications(trigger_data, n_intervals, current_toasts):
        try:
            if not current_user.is_authenticated:
                return []
            
            from app.modules.iperf.models import IperfSession
            now = time.time()
            new_toasts = []
            
            # 1. Mantener toasts actuales que NO hayan expirado (3 segundos de vida)
            if current_toasts:
                for t in current_toasts:
                    # Dash guarda el ID como un dict si se usó un dict en la creación
                    try:
                        t_ts = t.get("props", {}).get("id", {}).get("ts", 0)
                        if now - t_ts < 3:
                            new_toasts.append(t)
                    except:
                        continue

            # 2. Detectar disparador directo (Toast Trigger)
            ctx = callback_context
            if ctx.triggered:
                trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
                if trigger_id == "toast-trigger" and trigger_data:
                    new_toasts.append(_make_event_toast(
                        trigger_data.get("title", "SISTEMA"),
                        trigger_data.get("msg", ""),
                        trigger_data.get("type", "info"),
                        ts=now
                    ))

            # 3. Buscar sesiones terminadas no notificadas (Lógica de fondo)
            for sid, data in list(IperfService._live_data.items()):
                if sid not in IperfService._notified_sessions:
                    if data.get("summary"):
                        s = IperfSession.query.get(sid)
                        if s:
                            label = "SERVIDOR" if s.mode == "server" else "CLIENTE"
                            msg = f"Prueba finalizada con éxito ({s.protocol.upper()})"
                            new_toasts.append(_make_event_toast(f"TEST {label} OK", msg, "success", ts=now))
                            IperfService._notified_sessions.add(sid)

            return new_toasts[:3]
        except Exception as e:
            debug_logger.error(f"trigger_notifications: {e}")
            return []
