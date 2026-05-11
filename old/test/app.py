import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
from collections import deque
import threading
import subprocess
import re
import time
import socket
import io
import secrets
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from database import (
    init_schema, session_start, session_end,
    save_measurement, save_measurements_bulk, get_sessions,
    get_session_measurements, get_summary,
)
from report import generate_report

# ── Configuración ─────────────────────────────────────────────────────────────
MAX_POINTS   = 40     # puntos visibles en la gráfica (ventana deslizante)
SERVER_PORT  = 5201
API_PORT     = 8051   # puerto de la API REST
API_TOKEN    = secrets.token_hex(32)  # generado al arrancar; ver en consola

# ── Buffers compartidos ───────────────────────────────────────────────────────
timestamps  = deque(maxlen=MAX_POINTS)
recv_mbps   = deque(maxlen=MAX_POINTS)
sent_mbps   = deque(maxlen=MAX_POINTS)
jitter_ms   = deque(maxlen=MAX_POINTS)
retransmits = deque(maxlen=MAX_POINTS)
log_lines   = deque(maxlen=80)

server_proc  = None
client_proc  = None
lock         = threading.Lock()

# Estado compartido accesible desde callbacks y threads
state = {
    "mode":            "idle",
    "session_active":  False,
    "session_ended":   False,
    "db_session_id":   None,
    "db_enabled":      False,
    "last_report":     None,   # bytes del último PDF generado
    "last_session":    None,   # dict con datos de la última sesión
}

# ── Parser ────────────────────────────────────────────────────────────────────
DATA_RE = re.compile(
    r'\[(?P<id>\s*\d+|SUM)\]\s+'
    r'(?P<t0>\d+\.\d+)-(?P<t1>\d+\.\d+)\s+sec\s+'
    r'[\d.]+\s+\w+Bytes\s+'
    r'(?P<rate>[\d.]+)\s+(?P<unit>G|M|K)bits/sec'
    r'(?:\s+(?P<jitter>[\d.]+)\s+ms)?'
    r'(?:\s+(?P<lost>\d+)/\d+)?'
    r'.*?(?:\s+(?P<role>sender|receiver))?$'
)
SEP_RE      = re.compile(r'^[\s\-]+$')
LISTENING_RE = re.compile(r'Server listening on')
ACCEPTED_RE  = re.compile(r'Accepted connection from')

def to_mbps(v, u):
    return {"G": v * 1000, "M": v, "K": v / 1000}[u]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ── Utilidades ────────────────────────────────────────────────────────────────
def clear_buffers():
    timestamps.clear()
    recv_mbps.clear()
    sent_mbps.clear()
    jitter_ms.clear()
    retransmits.clear()

# ── Lector genérico ───────────────────────────────────────────────────────────
def iperf3_reader(proc, mode="server"):
    """
    Lee stdout de iperf3.
    Usa el separador '- - -' como señal de fin de grupo para garantizar
    que [SUM] siempre llega antes de hacer commit.

    En modo servidor también detecta:
      - 'Accepted connection from' → sesión iniciada
      - 'Server listening on'      → sesión terminada (cliente desconectado)
    """
    group = {"lines": [], "has_sum": False, "sum_data": None}

    def commit(data):
        ts = time.strftime('%H:%M:%S')
        with lock:
            timestamps.append(ts)
            recv_mbps.append(round(data["mbps"], 2))
            sent_mbps.append(round(data["mbps"], 2))
            jitter_ms.append(round(data["jitter"], 3) if data["jitter"] else 0)
            retransmits.append(data["retx"])
            # Guardar en MySQL si está habilitado
            if state["db_enabled"] and state["db_session_id"]:
                try:
                    save_measurement(
                        state["db_session_id"],
                        gbps        = round(data["mbps"] / 1000, 4),
                        jitter_ms   = round(data["jitter"], 3) if data["jitter"] else 0,
                        retransmits = data["retx"],
                    )
                except Exception as e:
                    log_lines.append(f"[DB] Error guardando medición: {e}")

    def flush_group():
        if group["has_sum"]:
            commit(group["sum_data"])
        elif group["lines"]:
            commit(group["lines"][-1])
        group["lines"].clear()
        group["has_sum"]  = False
        group["sum_data"] = None

    for raw in proc.stdout:
        line = raw.rstrip()
        if not line:
            continue
        with lock:
            log_lines.append(line)

        # Detección de eventos de sesión (solo servidor)
        if mode == "server":
            if ACCEPTED_RE.search(line):
                with lock:
                    state["session_active"] = True
                    state["last_session"] = {
                        "mode":       "server",
                        "port":       SERVER_PORT,
                        "protocol":   "tcp",
                        "parallel":   1,
                        "started_at": datetime.now().isoformat(),
                    }
                    clear_buffers()
                    if state["db_enabled"]:
                        try:
                            sid = session_start(
                                mode="server", port=SERVER_PORT, protocol="tcp")
                            state["db_session_id"] = sid
                            log_lines.append(f"[DB] Sesión #{sid} iniciada")
                        except Exception as e:
                            log_lines.append(f"[DB] Error abriendo sesión: {e}")
                continue
            if LISTENING_RE.search(line):
                with lock:
                    prev = state["session_active"]
                    state["session_active"] = False
                    if prev:
                        state["session_ended"] = True
                        if state["db_enabled"] and state["db_session_id"]:
                            try:
                                session_end(state["db_session_id"], "completed")
                                log_lines.append(f"[DB] Sesión #{state['db_session_id']} guardada")
                            except Exception as e:
                                log_lines.append(f"[DB] Error cerrando sesión: {e}")
                            state["db_session_id"] = None
                continue

        # Separador → flush del grupo completo
        if SEP_RE.match(line):
            flush_group()
            continue

        m = DATA_RE.search(line)
        if not m:
            continue

        t0  = float(m.group("t0"))
        t1  = float(m.group("t1"))
        dur = round(t1 - t0, 2)
        if dur < 0.5 or dur > 1.5:
            continue

        sid    = m.group("id").strip()
        mbps   = to_mbps(float(m.group("rate")), m.group("unit"))
        jitter = float(m.group("jitter")) if m.group("jitter") else None
        retx   = int(m.group("lost"))     if m.group("lost")   else 0
        role   = m.group("role") or ""
        data   = {"mbps": mbps, "jitter": jitter, "retx": retx}

        if mode == "client" and role == "receiver":
            continue
        if mode == "server" and role == "sender":
            continue

        if sid == "SUM":
            group["has_sum"]  = True
            group["sum_data"] = data
        else:
            group["lines"].append(data)

    flush_group()


# ── Control servidor ──────────────────────────────────────────────────────────
def port_is_listening(port: int) -> bool:
    """Verifica si hay algo escuchando en el puerto TCP dado."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_server(port=5201) -> tuple[bool, str]:
    """
    Levanta iperf3 -s y verifica que el puerto quede activo.
    Retorna (ok: bool, mensaje: str).
    """
    global server_proc, SERVER_PORT

    # ¿Ya hay un proceso corriendo?
    if server_proc and server_proc.poll() is None:
        return True, "Servidor ya activo"

    # ¿El puerto ya está ocupado por otro proceso?
    if port_is_listening(port):
        return False, f"Puerto {port} ya está en uso por otro proceso"

    SERVER_PORT = port
    server_proc = subprocess.Popen(
        ["iperf3", "-s", "-p", str(port), "--forceflush"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    threading.Thread(target=iperf3_reader, args=(server_proc, "server"), daemon=True).start()

    # Esperar hasta 2s a que el puerto quede activo
    for _ in range(8):
        time.sleep(0.25)
        if server_proc.poll() is not None:
            # El proceso murió → leer stderr para el mensaje
            out = ""
            try:
                out = server_proc.stdout.read(512)
            except Exception:
                pass
            server_proc = None
            return False, f"iperf3 falló al arrancar: {out.strip()}"
        if port_is_listening(port):
            return True, f"Servidor activo en puerto {port}"

    # Timeout — proceso vivo pero puerto aún no responde
    return False, f"Timeout: puerto {port} no responde tras 2s"

def stop_server():
    global server_proc
    if server_proc and server_proc.poll() is None:
        server_proc.terminate()
    server_proc = None
    with lock:
        state["session_active"] = False


# ── Control cliente ───────────────────────────────────────────────────────────
def run_client(host, port, duration, parallel, protocol, bandwidth):
    global client_proc
    cmd = ["iperf3", "-c", host, "-p", str(port),
           "-t", str(duration), "--forceflush", "-i", "1"]
    if parallel > 1:
        cmd += ["-P", str(parallel)]
    if protocol == "udp":
        cmd += ["-u", "-b", bandwidth]

    with lock:
        log_lines.append(f"▶ {' '.join(cmd)}")
        clear_buffers()
        state["last_session"] = {
            "mode":       "client",
            "host":       host,
            "port":       port,
            "protocol":   protocol,
            "parallel":   parallel,
            "duration_s": duration,
            "started_at": datetime.now().isoformat(),
        }
        if state["db_enabled"]:
            try:
                sid = session_start(
                    mode="client", port=port, protocol=protocol,
                    parallel=parallel, host=host, duration_s=duration)
                state["db_session_id"] = sid
                log_lines.append(f"[DB] Sesión #{sid} iniciada")
            except Exception as e:
                log_lines.append(f"[DB] Error abriendo sesión: {e}")

    client_proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    iperf3_reader(client_proc, mode="client")
    with lock:
        log_lines.append("✓ Test finalizado")
        state["session_ended"] = True
        if state["db_enabled"] and state["db_session_id"]:
            try:
                session_end(state["db_session_id"], "completed")
                log_lines.append(f"[DB] Sesión #{state['db_session_id']} guardada")
            except Exception as e:
                log_lines.append(f"[DB] Error cerrando sesión: {e}")
            state["db_session_id"] = None

def start_client(host, port, duration, parallel, protocol, bandwidth):
    threading.Thread(
        target=run_client,
        args=(host, port, duration, parallel, protocol, bandwidth),
        daemon=True,
    ).start()

def stop_client():
    global client_proc
    if client_proc and client_proc.poll() is None:
        client_proc.terminate()
    client_proc = None


# ── Estilos ───────────────────────────────────────────────────────────────────
DARK_BG = "#0f1117"
CARD_BG = "#1a1d2e"
ACCENT  = "#00d4ff"
GREEN   = "#00ff9d"
YELLOW  = "#ffd166"
RED_C   = "#ff6b6b"
TEXT    = "#e2e8f0"
MUTED   = "#64748b"
BORDER  = "#2d3748"

card  = {"background": CARD_BG, "borderRadius": "12px",
         "padding": "20px", "border": f"1px solid {BORDER}"}
mcard = {**card, "textAlign": "center", "flex": "1", "minWidth": "140px"}

badge_off    = {"fontSize": "12px", "padding": "6px 14px", "borderRadius": "20px",
                "background": "#1a2a1a", "color": MUTED, "border": f"1px solid {BORDER}"}
badge_server = {**badge_off, "background": "#1a3a1a", "color": GREEN,  "border": f"1px solid {GREEN}"}
badge_session= {**badge_off, "background": "#2a3a1a", "color": "#aaff44", "border": f"1px solid #aaff44"}
badge_client = {**badge_off, "background": "#1a2a3a", "color": ACCENT, "border": f"1px solid {ACCENT}"}

def btn(color, outline=False):
    if outline:
        return {"background": "transparent", "color": color, "border": f"2px solid {color}",
                "borderRadius": "8px", "padding": "7px 18px", "cursor": "pointer",
                "fontWeight": "700", "fontSize": "13px"}
    return {"background": color, "color": "#0f1117", "border": "none",
            "borderRadius": "8px", "padding": "8px 20px", "cursor": "pointer",
            "fontWeight": "700", "fontSize": "13px"}

def input_style(w="100%"):
    return {"background": "#0d1117", "color": TEXT, "border": f"1px solid {BORDER}",
            "borderRadius": "6px", "padding": "6px 10px", "fontSize": "13px",
            "width": w, "fontFamily": "inherit", "boxSizing": "border-box"}

def empty_graph(small=False):
    m  = dict(l=44, r=8, t=4, b=32) if small else dict(l=48, r=12, t=8, b=36)
    fs = 9 if small else 10
    return {"data": [], "layout": go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=m,
        xaxis=dict(showgrid=False, color=MUTED, tickfont=dict(size=fs)),
        yaxis=dict(gridcolor=BORDER, color=MUTED, tickfont=dict(size=fs)),
    )}

LOCAL_IP = get_local_ip()

# ── Layout ────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="iperf3 Dashboard",
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

app.layout = html.Div(
    style={"background": DARK_BG, "minHeight": "100vh",
           "fontFamily": "'JetBrains Mono','Fira Code',monospace",
           "color": TEXT, "padding": "24px"},
    children=[

    html.Div(style={"display": "flex", "alignItems": "center",
                    "justifyContent": "space-between", "marginBottom": "24px"}, children=[
        html.Div(children=[
            html.H1("⚡ iperf3 Dashboard",
                    style={"margin": "0", "fontSize": "24px", "color": ACCENT}),
            html.P(f"IP local: {LOCAL_IP}",
                   style={"margin": "4px 0 0", "fontSize": "12px", "color": MUTED}),
        ]),
        html.Div(id="status-badge", style=badge_off, children="● INACTIVO"),
    ]),

    html.Div(style={"display": "flex", "gap": "8px", "marginBottom": "20px"}, children=[
        html.Button("🖥  Servidor", id="tab-server", n_clicks=0, style=btn(GREEN)),
        html.Button("📡  Cliente",  id="tab-client", n_clicks=0, style=btn(GREEN, outline=True)),
    ]),

    # Panel Servidor
    html.Div(id="panel-server", children=[
        html.Div(style={**card, "marginBottom": "20px", "display": "flex",
                        "gap": "16px", "alignItems": "flex-end", "flexWrap": "wrap"}, children=[
            html.Div(children=[
                html.P("Puerto", style={"margin": "0 0 4px", "fontSize": "11px",
                                        "color": MUTED, "textTransform": "uppercase"}),
                dcc.Input(id="srv-port", type="number", value=SERVER_PORT,
                          style=input_style("100px")),
            ]),
            html.Button("▶ Levantar servidor", id="btn-srv-start", n_clicks=0, style=btn(GREEN)),
            html.Button("■ Detener",           id="btn-srv-stop",  n_clicks=0, style=btn(RED_C)),
        ]),
        html.Div(style={**card, "marginBottom": "20px"}, children=[
            html.P("Conectar desde otro host:", style={"margin": "0 0 8px", "fontSize": "11px",
                                                        "color": MUTED, "textTransform": "uppercase"}),
            html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}, children=[
                html.Code(id="srv-cmd-tcp",
                          style={"fontSize": "13px", "color": GREEN, "background": "#0d1117",
                                 "padding": "6px 12px", "borderRadius": "6px",
                                 "border": f"1px solid {BORDER}"}),
                html.Code(id="srv-cmd-parallel",
                          style={"fontSize": "13px", "color": ACCENT, "background": "#0d1117",
                                 "padding": "6px 12px", "borderRadius": "6px",
                                 "border": f"1px solid {BORDER}"}),
                html.Code(id="srv-cmd-udp",
                          style={"fontSize": "13px", "color": YELLOW, "background": "#0d1117",
                                 "padding": "6px 12px", "borderRadius": "6px",
                                 "border": f"1px solid {BORDER}"}),
            ]),
        ]),
    ]),

    # Panel Cliente
    html.Div(id="panel-client", style={"display": "none"}, children=[
        html.Div(style={**card, "marginBottom": "20px"}, children=[
            html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap",
                            "alignItems": "flex-end"}, children=[
                html.Div(children=[
                    html.P("Host destino", style={"margin": "0 0 4px", "fontSize": "11px",
                                                   "color": MUTED, "textTransform": "uppercase"}),
                    dcc.Input(id="cli-host", type="text", value="127.0.0.1",
                              placeholder="192.168.1.100", style=input_style("160px")),
                ]),
                html.Div(children=[
                    html.P("Puerto", style={"margin": "0 0 4px", "fontSize": "11px",
                                            "color": MUTED, "textTransform": "uppercase"}),
                    dcc.Input(id="cli-port", type="number", value=SERVER_PORT,
                              style=input_style("80px")),
                ]),
                html.Div(children=[
                    html.P("Duración (s)", style={"margin": "0 0 4px", "fontSize": "11px",
                                                   "color": MUTED, "textTransform": "uppercase"}),
                    dcc.Input(id="cli-duration", type="number", value=30, min=1,
                              style=input_style("80px")),
                ]),
                html.Div(children=[
                    html.P("Streams -P", style={"margin": "0 0 4px", "fontSize": "11px",
                                                 "color": MUTED, "textTransform": "uppercase"}),
                    dcc.Input(id="cli-parallel", type="number", value=1, min=1, max=128,
                              style=input_style("70px")),
                ]),
                html.Div(children=[
                    html.P("Protocolo", style={"margin": "0 0 4px", "fontSize": "11px",
                                               "color": MUTED, "textTransform": "uppercase"}),
                    dcc.Dropdown(id="cli-protocol",
                                 options=[{"label": "TCP", "value": "tcp"},
                                          {"label": "UDP", "value": "udp"}],
                                 value="tcp", clearable=False,
                                 style={"width": "90px", "fontSize": "13px"}),
                ]),
                html.Div(id="cli-bw-wrap", style={"display": "none"}, children=[
                    html.P("Ancho de banda", style={"margin": "0 0 4px", "fontSize": "11px",
                                                     "color": MUTED, "textTransform": "uppercase"}),
                    dcc.Input(id="cli-bandwidth", type="text", value="100M",
                              style=input_style("90px")),
                ]),
                html.Button("▶ Iniciar test", id="btn-cli-start", n_clicks=0, style=btn(ACCENT)),
                html.Button("■ Detener",      id="btn-cli-stop",  n_clicks=0, style=btn(RED_C)),
            ]),
        ]),
    ]),

    # Métricas
    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "20px",
                    "flexWrap": "wrap"}, children=[
        html.Div(style=mcard, children=[
            html.P("Throughput", style={"margin": "0 0 6px", "fontSize": "11px", "color": MUTED,
                                        "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.H2(id="m-tp", children="—", style={"margin": "0", "fontSize": "28px", "color": ACCENT}),
            html.P("Gbits/sec", style={"margin": "4px 0 0", "fontSize": "11px", "color": MUTED}),
        ]),
        html.Div(style=mcard, children=[
            html.P("Jitter", style={"margin": "0 0 6px", "fontSize": "11px", "color": MUTED,
                                    "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.H2(id="m-jit", children="—", style={"margin": "0", "fontSize": "28px", "color": YELLOW}),
            html.P("ms (UDP)", style={"margin": "4px 0 0", "fontSize": "11px", "color": MUTED}),
        ]),
        html.Div(style=mcard, children=[
            html.P("Retransmisiones", style={"margin": "0 0 6px", "fontSize": "11px", "color": MUTED,
                                             "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.H2(id="m-retx", children="—", style={"margin": "0", "fontSize": "28px", "color": RED_C}),
            html.P("acumuladas", style={"margin": "4px 0 0", "fontSize": "11px", "color": MUTED}),
        ]),
        html.Div(style=mcard, children=[
            html.P("Muestras", style={"margin": "0 0 6px", "fontSize": "11px", "color": MUTED,
                                      "textTransform": "uppercase", "letterSpacing": "1px"}),
            html.H2(id="m-cnt", children="—", style={"margin": "0", "fontSize": "28px", "color": TEXT}),
            html.P(f"ventana {MAX_POINTS}s", style={"margin": "4px 0 0", "fontSize": "11px", "color": MUTED}),
        ]),
    ]),

    # Gráficas
    html.Div(style={**card, "marginBottom": "16px"}, children=[
        html.P("Throughput (Gbits/sec)", style={"margin": "0 0 14px", "fontSize": "12px",
                                                "color": MUTED, "textTransform": "uppercase",
                                                "letterSpacing": "1px"}),
        dcc.Graph(id="g-tp", config={"displayModeBar": False},
                  style={"height": "220px"}, figure=empty_graph()),
    ]),

    html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap",
                    "marginBottom": "16px"}, children=[
        html.Div(style={**card, "flex": "1", "minWidth": "280px"}, children=[
            html.P("Jitter (ms) · UDP", style={"margin": "0 0 14px", "fontSize": "12px",
                                               "color": MUTED, "textTransform": "uppercase",
                                               "letterSpacing": "1px"}),
            dcc.Graph(id="g-jit", config={"displayModeBar": False},
                      style={"height": "180px"}, figure=empty_graph(small=True)),
        ]),
        html.Div(style={**card, "flex": "1", "minWidth": "280px"}, children=[
            html.P("Retransmisiones · TCP", style={"margin": "0 0 14px", "fontSize": "12px",
                                                   "color": MUTED, "textTransform": "uppercase",
                                                   "letterSpacing": "1px"}),
            dcc.Graph(id="g-retx", config={"displayModeBar": False},
                      style={"height": "180px"}, figure=empty_graph(small=True)),
        ]),
    ]),

    html.Div(style=card, children=[
        html.P("Log iperf3", style={"margin": "0 0 10px", "fontSize": "12px", "color": MUTED,
                                    "textTransform": "uppercase", "letterSpacing": "1px"}),
        html.Pre(id="log-box", children="Esperando...",
                 style={"margin": "0", "fontSize": "11px", "color": "#94a3b8",
                        "background": "#0d1117", "padding": "12px", "borderRadius": "8px",
                        "height": "180px", "overflowY": "auto",
                        "border": f"1px solid {BORDER}", "whiteSpace": "pre-wrap"}),
    ]),

    dcc.Interval(id="interval", interval=1000, n_intervals=0, disabled=False),
    dcc.Store(id="store-mode", data="idle"),

    # ── Modal fin de prueba ───────────────────────────────────────────────────
    html.Div(id="modal", style={"display": "none"}, children=[
        html.Div(style={
            "position": "fixed", "top": "0", "left": "0",
            "width": "100%", "height": "100%",
            "background": "rgba(0,0,0,0.7)", "zIndex": "999",
        }),
        html.Div(style={
            "position": "fixed", "top": "50%", "left": "50%",
            "transform": "translate(-50%, -50%)",
            "background": CARD_BG, "borderRadius": "16px",
            "padding": "36px 40px", "zIndex": "1000",
            "border": f"1px solid {GREEN}", "minWidth": "360px",
            "textAlign": "center", "boxShadow": f"0 0 40px rgba(0,255,157,0.2)",
        }, children=[
            html.Div("✓", style={"fontSize": "48px", "color": GREEN, "marginBottom": "12px"}),
            html.H2("Prueba finalizada", style={"margin": "0 0 8px", "color": TEXT, "fontSize": "20px"}),
            html.P(id="modal-msg", style={"margin": "0 0 24px", "color": MUTED, "fontSize": "13px"}),
            html.Div(style={"display": "flex", "gap": "12px", "justifyContent": "center"}, children=[
                html.A(
                    "⬇ Descargar PDF",
                    href="/api/report/download",
                    target="_blank",
                    style={
                        "background": ACCENT, "color": "#0f1117",
                        "border": "none", "borderRadius": "8px",
                        "padding": "10px 24px", "cursor": "pointer",
                        "fontWeight": "700", "fontSize": "13px",
                        "textDecoration": "none", "display": "inline-block",
                        "fontFamily": "inherit",
                    }
                ),
                html.Button("Cerrar", id="btn-modal-close", n_clicks=0,
                            style={**btn(GREEN), "padding": "10px 32px", "fontSize": "14px"}),
            ]),
        ]),
    ]),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("panel-server", "style"),
    Output("panel-client", "style"),
    Output("tab-server",   "style"),
    Output("tab-client",   "style"),
    Input("tab-server", "n_clicks"),
    Input("tab-client", "n_clicks"),
    prevent_initial_call=True,
)
def switch_tab(n_srv, n_cli):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    tab = ctx.triggered[0]["prop_id"]
    if "tab-server" in tab:
        return ({}, {"display": "none"}, btn(GREEN), btn(GREEN, outline=True))
    else:
        return ({"display": "none"}, {}, btn(GREEN, outline=True), btn(GREEN))


@app.callback(
    Output("cli-bw-wrap", "style"),
    Input("cli-protocol", "value"),
)
def toggle_bandwidth(protocol):
    return {} if protocol == "udp" else {"display": "none"}


@app.callback(
    Output("srv-cmd-tcp",      "children"),
    Output("srv-cmd-parallel", "children"),
    Output("srv-cmd-udp",      "children"),
    Input("srv-port", "value"),
)
def update_cmds(port):
    p = port or SERVER_PORT
    return (
        f"iperf3 -c {LOCAL_IP} -p {p} -t 30",
        f"iperf3 -c {LOCAL_IP} -p {p} -P 4 -t 30",
        f"iperf3 -c {LOCAL_IP} -p {p} -u -b 100M -t 30",
    )


@app.callback(
    Output("store-mode",   "data", allow_duplicate=True),
    Output("status-badge", "children", allow_duplicate=True),
    Output("status-badge", "style",    allow_duplicate=True),
    Input("btn-srv-start", "n_clicks"),
    Input("btn-srv-stop",  "n_clicks"),
    Input("btn-cli-start", "n_clicks"),
    Input("btn-cli-stop",  "n_clicks"),
    State("store-mode",    "data"),
    State("srv-port",      "value"),
    State("cli-host",      "value"),
    State("cli-port",      "value"),
    State("cli-duration",  "value"),
    State("cli-parallel",  "value"),
    State("cli-protocol",  "value"),
    State("cli-bandwidth", "value"),
    prevent_initial_call=True,
)
def control(n_ss, n_sp, n_cs, n_cp, mode,
            srv_port, cli_host, cli_port, cli_dur, cli_par, cli_proto, cli_bw):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    bid = ctx.triggered[0]["prop_id"]

    if "btn-srv-start" in bid and mode == "idle":
        ok, msg = start_server(srv_port or 5201)
        if ok:
            with lock:
                state["mode"] = "server"
                log_lines.append(f"✓ {msg}")
            return "server", "● SERVIDOR ACTIVO", badge_server
        else:
            with lock:
                log_lines.append(f"✗ {msg}")
            # No cambiar modo — quedarse en idle y mostrar error en badge
            return "idle", f"✗ {msg[:30]}", {**badge_off, "color": RED_C, "border": f"1px solid {RED_C}"}

    if "btn-srv-stop" in bid and mode == "server":
        stop_server()
        with lock:
            state["mode"] = "idle"
        return "idle", "● INACTIVO", badge_off

    if "btn-cli-start" in bid and mode == "idle":
        start_client(cli_host or "127.0.0.1", cli_port or 5201,
                     cli_dur or 30, cli_par or 1,
                     cli_proto or "tcp", cli_bw or "100M")
        with lock:
            state["mode"] = "client"
        return "client", "● TEST ACTIVO", badge_client

    if "btn-cli-stop" in bid and mode == "client":
        stop_client()
        with lock:
            state["mode"] = "idle"
        return "idle", "● INACTIVO", badge_off

    raise dash.exceptions.PreventUpdate


@app.callback(
    Output("g-tp",         "figure"),
    Output("g-jit",        "figure"),
    Output("g-retx",       "figure"),
    Output("m-tp",         "children"),
    Output("m-jit",        "children"),
    Output("m-retx",       "children"),
    Output("m-cnt",        "children"),
    Output("log-box",      "children"),
    Output("store-mode",   "data"),
    Output("status-badge", "children"),
    Output("status-badge", "style"),
    Output("modal",        "style"),
    Output("modal-msg",    "children"),
    Input("interval", "n_intervals"),
    State("store-mode", "data"),
    prevent_initial_call=True,
)
def refresh(_, mode):
    new_mode    = mode
    new_badge   = dash.no_update
    new_bstyle  = dash.no_update
    modal_style = {"display": "none"}
    modal_msg   = ""
    just_ended  = False

    with lock:
        ended = state["session_ended"]
        if ended:
            state["session_ended"] = False
            just_ended = True

    # ── Fin de test cliente ────────────────────────────────────────────────────
    if mode == "client" and client_proc is not None and client_proc.poll() is not None:
        new_mode   = "idle"
        new_badge  = "● INACTIVO"
        new_bstyle = badge_off
        just_ended = True
        with lock:
            state["mode"] = "idle"

    # ── Badge servidor + detección de caída inesperada ────────────────────────
    if mode == "server":
        if server_proc is not None and server_proc.poll() is not None:
            # El proceso murió sin que el usuario presionara Detener
            with lock:
                state["mode"] = "idle"
                state["session_active"] = False
                log_lines.append("✗ El servidor iperf3 se cerró inesperadamente")
            new_mode   = "idle"
            new_badge  = "✗ SERVIDOR CAÍDO"
            new_bstyle = {**badge_off, "color": RED_C, "border": f"1px solid {RED_C}"}
        elif not port_is_listening(SERVER_PORT):
            # Proceso vivo pero puerto no responde (raro, pero posible)
            new_badge  = "⚠ PUERTO NO RESPONDE"
            new_bstyle = {**badge_off, "color": YELLOW, "border": f"1px solid {YELLOW}"}
        else:
            with lock:
                sess = state["session_active"]
            new_badge  = "● SESIÓN ACTIVA"  if sess else "● SERVIDOR ACTIVO"
            new_bstyle = badge_session       if sess else badge_server

    # ── Si acaba de terminar → generar PDF, limpiar gráficas y mostrar modal ────
    if just_ended:
        with lock:
            ts_snap   = list(timestamps)
            rx_snap   = list(recv_mbps)
            jit_snap  = list(jitter_ms)
            retx_snap = list(retransmits)
            sess_snap = dict(state.get("last_session") or {})
            clear_buffers()

        avg_gbps   = round(sum(rx_snap) / len(rx_snap) / 1000, 3) if rx_snap else 0
        max_gbps   = round(max(rx_snap) / 1000, 3) if rx_snap else 0
        min_gbps   = round(min(rx_snap) / 1000, 3) if rx_snap else 0
        jit_nonzero= [j for j in jit_snap if j > 0]
        avg_jit    = round(sum(jit_nonzero) / len(jit_nonzero), 3) if jit_nonzero else 0
        total_retx = sum(retx_snap)

        modal_msg = f"Throughput promedio: {avg_gbps} Gbits/sec"
        if avg_jit > 0:
            modal_msg += f"  ·  Jitter: {avg_jit} ms"
        if total_retx > 0:
            modal_msg += f"  ·  Retransmisiones: {total_retx}"

        # Construir session_data para el PDF
        now = datetime.now()
        session_data = {
            **sess_snap,
            "avg_gbps":          avg_gbps,
            "max_gbps":          max_gbps,
            "min_gbps":          min_gbps,
            "avg_jitter_ms":     avg_jit,
            "total_retransmits": total_retx,
            "total_samples":     len(ts_snap),
            "ended_at":          now.isoformat(),
        }
        if "started_at" not in session_data:
            session_data["started_at"] = now.isoformat()

        gbps_vals = [round(v / 1000, 3) for v in rx_snap]

        # Generar PDF en background para no bloquear el callback
        try:
            pdf_bytes = generate_report(
                session_data, ts_snap, gbps_vals, jit_snap, retx_snap)
            with lock:
                state["last_report"] = pdf_bytes
        except Exception as e:
            with lock:
                log_lines.append(f"[PDF] Error generando reporte: {e}")

        modal_style = {"display": "block"}

        return (
            empty_graph(), empty_graph(small=True), empty_graph(small=True),
            "—", "—", "—", "—",
            "\n".join(log_lines),
            new_mode, new_badge, new_bstyle,
            modal_style, modal_msg,
        )

    # ── Refresh normal ─────────────────────────────────────────────────────────
    with lock:
        ts   = list(timestamps)
        rx   = list(recv_mbps)
        jit  = list(jitter_ms)
        retx = list(retransmits)
        log  = "\n".join(log_lines) or "Sin actividad aún..."

    def layout(small=False):
        m  = dict(l=44, r=8, t=4, b=32) if small else dict(l=48, r=12, t=8, b=36)
        fs = 9 if small else 10
        d  = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  margin=m, hovermode="x unified",
                  xaxis=dict(showgrid=False, color=MUTED, tickfont=dict(size=fs)),
                  yaxis=dict(gridcolor=BORDER, color=MUTED, tickfont=dict(size=fs)))
        if not small:
            d["legend"] = dict(font=dict(color=MUTED, size=11))
        return d

    rx_gbps = [round(v / 1000, 3) for v in rx]

    fig_tp = go.Figure(layout=go.Layout(**layout()))
    if rx_gbps:
        fig_tp.add_trace(go.Scatter(
            x=ts, y=rx_gbps, name="Throughput",
            line=dict(color=ACCENT, width=2),
            fill="tozeroy", fillcolor="rgba(0,212,255,0.08)"))

    jit_vals = [v for v in jit if v > 0]
    jit_ts   = [ts[i] for i, v in enumerate(jit) if v > 0]
    fig_jit  = go.Figure(layout=go.Layout(**layout(small=True)))
    if jit_vals:
        fig_jit.add_trace(go.Scatter(
            x=jit_ts, y=jit_vals, name="Jitter",
            line=dict(color=YELLOW, width=2),
            fill="tozeroy", fillcolor="rgba(255,209,102,0.08)"))

    fig_retx = go.Figure(layout=go.Layout(**layout(small=True)))
    if retx:
        fig_retx.add_trace(go.Bar(x=ts, y=retx, marker_color=RED_C, opacity=0.8))

    return (
        fig_tp, fig_jit, fig_retx,
        f"{rx_gbps[-1]:.2f}" if rx_gbps else "—",
        f"{jit_vals[-1]:.3f}" if jit_vals else "—",
        str(sum(retx)) if retx else "—",
        str(len(ts)),
        log,
        new_mode, new_badge, new_bstyle,
        modal_style, modal_msg,
    )


@app.callback(
    Output("modal", "style", allow_duplicate=True),
    Input("btn-modal-close", "n_clicks"),
    prevent_initial_call=True,
)
def close_modal(_):
    return {"display": "none"}


# ── API REST ──────────────────────────────────────────────────────────────────
flask_api = Flask("iperf3_api")

def require_token(f):
    """Decorador: valida Bearer token en Authorization header."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] != API_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

def api_state_snapshot():
    with lock:
        return {
            "mode":           state["mode"],
            "session_active": state["session_active"],
            "samples":        len(timestamps),
            "last_gbps":      round(list(recv_mbps)[-1] / 1000, 3) if recv_mbps else None,
        }

# ── GET /api/status ───────────────────────────────────────────────────────────
@flask_api.route("/api/status", methods=["GET"])
@require_token
def api_status():
    """Retorna el estado actual del dashboard."""
    return jsonify(api_state_snapshot())

# ── POST /api/server/start ────────────────────────────────────────────────────
@flask_api.route("/api/server/start", methods=["POST"])
@require_token
def api_server_start():
    """
    Levanta el servidor iperf3.
    Body JSON opcional: { "port": 5201 }
    """
    if state["mode"] != "idle":
        return jsonify({"error": f"Ocupado en modo '{state['mode']}'"}), 409
    body = request.get_json(silent=True) or {}
    port = int(body.get("port", SERVER_PORT))
    start_server(port)
    with lock:
        state["mode"] = "server"
    return jsonify({"ok": True, "port": port})

# ── POST /api/server/stop ─────────────────────────────────────────────────────
@flask_api.route("/api/server/stop", methods=["POST"])
@require_token
def api_server_stop():
    """Detiene el servidor iperf3."""
    if state["mode"] != "server":
        return jsonify({"error": "El servidor no está activo"}), 409
    stop_server()
    with lock:
        state["mode"] = "idle"
    return jsonify({"ok": True})

# ── POST /api/client/start ────────────────────────────────────────────────────
@flask_api.route("/api/client/start", methods=["POST"])
@require_token
def api_client_start():
    """
    Inicia un test como cliente.
    Body JSON: {
      "host":      "192.168.1.100",   # requerido
      "port":      5201,
      "duration":  30,
      "parallel":  1,
      "protocol":  "tcp",             # "tcp" | "udp"
      "bandwidth": "100M"             # solo UDP
    }
    """
    if state["mode"] != "idle":
        return jsonify({"error": f"Ocupado en modo '{state['mode']}'"}), 409
    body = request.get_json(silent=True) or {}
    host = body.get("host")
    if not host:
        return jsonify({"error": "Campo 'host' requerido"}), 400
    port      = int(body.get("port",      5201))
    duration  = int(body.get("duration",  30))
    parallel  = int(body.get("parallel",  1))
    protocol  = body.get("protocol",  "tcp")
    bandwidth = body.get("bandwidth", "100M")
    start_client(host, port, duration, parallel, protocol, bandwidth)
    with lock:
        state["mode"] = "client"
    return jsonify({"ok": True, "host": host, "port": port,
                    "duration": duration, "parallel": parallel,
                    "protocol": protocol})

# ── POST /api/client/stop ─────────────────────────────────────────────────────
@flask_api.route("/api/client/stop", methods=["POST"])
@require_token
def api_client_stop():
    """Detiene el test de cliente en curso."""
    if state["mode"] != "client":
        return jsonify({"error": "No hay test de cliente activo"}), 409
    stop_client()
    with lock:
        state["mode"] = "idle"
    return jsonify({"ok": True})

# ── GET /api/results ──────────────────────────────────────────────────────────
@flask_api.route("/api/results", methods=["GET"])
@require_token
def api_results():
    """Retorna los últimos N puntos de datos."""
    with lock:
        ts   = list(timestamps)
        rx   = [round(v / 1000, 3) for v in recv_mbps]
        jit  = list(jitter_ms)
        retx = list(retransmits)
    return jsonify({
        "timestamps":  ts,
        "gbps":        rx,
        "jitter_ms":   jit,
        "retransmits": retx,
    })

@flask_api.route("/api/report/download", methods=["GET"])
def api_report_download():
    """
    Descarga el PDF del último reporte generado.
    No requiere token — el link se abre desde el modal del dashboard.
    """
    with lock:
        pdf_bytes = state.get("last_report")
    if not pdf_bytes:
        return "No hay reporte disponible todavía.", 404

    buf = io.BytesIO(pdf_bytes)
    filename = f"iperf3_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


def run_api():
    flask_api.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False)


# ── Endpoints de reporte ──────────────────────────────────────────────────────

@flask_api.route("/api/reports/sessions", methods=["GET"])
@require_token
def api_report_sessions():
    """
    Lista las últimas sesiones con su resumen.
    Query params opcionales: ?limit=50&mode=server|client
    """
    if not state["db_enabled"]:
        return jsonify({"error": "Base de datos no disponible"}), 503
    limit = int(request.args.get("limit", 50))
    mode  = request.args.get("mode", None)
    rows  = get_sessions(limit=limit, mode=mode)
    # Convertir datetimes a string para JSON
    for r in rows:
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return jsonify(rows)


@flask_api.route("/api/reports/sessions/<int:session_id>", methods=["GET"])
@require_token
def api_report_session_detail(session_id):
    """Retorna el resumen y todos los puntos de una sesión específica."""
    if not state["db_enabled"]:
        return jsonify({"error": "Base de datos no disponible"}), 503
    summary = get_summary(session_id)
    if not summary:
        return jsonify({"error": "Sesión no encontrada"}), 404
    measurements = get_session_measurements(session_id)
    for k, v in summary.items():
        if hasattr(v, "isoformat"):
            summary[k] = v.isoformat()
    for m in measurements:
        for k, v in m.items():
            if hasattr(v, "isoformat"):
                m[k] = v.isoformat()
    return jsonify({"summary": summary, "measurements": measurements})


if __name__ == "__main__":
    # Intentar conectar a MySQL al arrancar
    try:
        init_schema()
        with lock:
            state["db_enabled"] = True
        print("[DB] Conexión a MySQL exitosa.")
    except Exception as e:
        print(f"[DB] MySQL no disponible, reportes deshabilitados: {e}")

    print("=" * 60)
    print(f"  Dashboard : http://0.0.0.0:8050")
    print(f"  API REST  : http://0.0.0.0:{API_PORT}")
    print(f"  API Token : {API_TOKEN}")
    print(f"  MySQL     : {'✓ conectado' if state['db_enabled'] else '✗ no disponible'}")
    print("=" * 60)
    threading.Thread(target=run_api, daemon=True).start()
    app.run(debug=False, host="0.0.0.0", port=8050)
