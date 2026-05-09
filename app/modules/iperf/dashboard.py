import dash
from dash import html, dcc, Input, Output, State, callback_context
import plotly.graph_objs as go
from collections import deque
import threading
import time
import json
from datetime import datetime
from app.modules.iperf.services import IperfService

# Estructuras de datos globales para el dashboard (similares a la demo)
MAX_POINTS = 60
timestamps = deque(maxlen=MAX_POINTS)
recv_mbps = deque(maxlen=MAX_POINTS)
jitter_ms = deque(maxlen=MAX_POINTS)
retransmits = deque(maxlen=MAX_POINTS)
log_lines = deque(maxlen=100)
lock = threading.Lock()

def init_dashboard(server):
    """Inicializa Dash dentro del servidor Flask."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/iperf/dashboard/',
        external_stylesheets=[
            "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
    )

    # ─── Estilos Nexus (Tokens traducidos) ───────────────────────────────────────
    DARK_BG = "#0f1117"
    CARD_BG = "#1a1d2e"
    ACCENT  = "#2563eb" # Primary Blue
    GREEN   = "#10b981"
    YELLOW  = "#f59e0b"
    RED_C   = "#ef4444"
    TEXT    = "#e2e8f0"
    MUTED   = "#64748b"
    BORDER  = "rgba(255,255,255,0.1)"

    def empty_graph(small=False):
        m = dict(l=44, r=8, t=4, b=32) if small else dict(l=48, r=12, t=8, b=36)
        fs = 9 if small else 10
        return {"data": [], "layout": go.Layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=m,
            xaxis=dict(showgrid=False, color=MUTED, tickfont=dict(size=fs)),
            yaxis=dict(gridcolor=BORDER, color=MUTED, tickfont=dict(size=fs)),
        )}

    # ─── Layout ───────────────────────────────────────────────────────────────────
    dash_app.layout = html.Div(
        className="min-h-screen p-6 text-gray-200",
        style={"backgroundColor": DARK_BG, "fontFamily": "'Inter', sans-serif"},
        children=[
            # Header
            html.Div(className="flex flex-col mb-8", children=[
                html.H1("NETWORK PERFORMANCE", className="text-3xl font-black text-blue-600 tracking-tighter italic uppercase"),
                html.P("iperf3 Orchestration & Analysis", className="text-xs font-black text-gray-500 uppercase tracking-widest"),
            ]),

            # Controls
            html.Div(className="flex items-center justify-between p-4 mb-8 border bg-gray-900 bg-opacity-40 rounded-2xl border-white border-opacity-10 backdrop-blur-sm", children=[
                html.Div(className="flex items-center gap-6", children=[
                    html.Div(id="status-badge", className="flex items-center gap-3 px-4 py-2 border rounded-xl bg-gray-800 border-white border-opacity-10 shadow-inner", children=[
                        html.Div(id="status-dot", className="w-3 h-3 rounded-full bg-red-500 shadow-lg"),
                        html.Span(id="status-text", children="SERVER OFFLINE", className="text-xs font-bold text-red-500 uppercase tracking-widest")
                    ]),
                    html.Div(className="h-8 w-px bg-white bg-opacity-10"),
                    html.P(f"MASTER NODE: 127.0.0.1:5201", className="text-xs font-black text-gray-500 uppercase tracking-widest"),
                ]),
                html.Div(className="flex gap-4", children=[
                    html.Button([html.I(className="fas fa-play mr-2"), "START SERVER"], id="btn-start", className="px-6 py-2 text-xs font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all shadow-lg shadow-blue-900/20"),
                    html.Button([html.I(className="fas fa-stop mr-2"), "STOP SERVER"], id="btn-stop", className="px-6 py-2 text-xs font-bold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-all shadow-lg shadow-red-900/20"),
                ])
            ]),

            # Main Grid
            html.Div(className="grid grid-cols-1 md:grid-cols-10 gap-6", children=[
                # Left: Console (60%)
                html.Div(className="md:col-span-6 flex flex-col min-h-[500px]", children=[
                    html.Div(className="flex-1 bg-black bg-opacity-90 border border-white border-opacity-10 rounded-3xl overflow-hidden flex flex-col shadow-2xl", children=[
                        html.Div(className="flex items-center justify-between px-6 py-4 border-b border-white border-opacity-5 bg-white bg-opacity-5", children=[
                            html.Div(className="flex items-center gap-3", children=[
                                html.I(className="fas fa-terminal text-blue-500 text-xs"),
                                html.Span("SYSTEM OUTPUT: iperf3_server.log", className="text-xs font-bold text-gray-400 uppercase tracking-widest")
                            ]),
                            html.Button("CLEAR CONSOLE", id="btn-clear", className="text-xs font-bold text-gray-600 hover:text-blue-500 transition-colors")
                        ]),
                        html.Div(id="log-container", className="flex-1 p-6 font-mono text-sm overflow-y-auto", children=[
                            html.Pre(id="log-output", className="text-emerald-500 leading-relaxed whitespace-pre-wrap", children="Waiting for server activity...")
                        ]),
                        html.Div(className="px-6 py-2 border-t border-white border-opacity-5 bg-white bg-opacity-2 flex justify-between items-center", children=[
                            html.P("nexus@iperf-server:~$ tail -f logs/iperf3.log", className="text-xs font-mono text-gray-700 uppercase tracking-widest"),
                            html.P(id="last-update", children="LAST UPDATE: --:--:--", className="text-xs font-mono text-gray-700 uppercase tracking-widest")
                        ])
                    ])
                ]),

                # Right: Stats (40%)
                html.Div(className="md:col-span-4 flex flex-col gap-6", children=[
                    # Throughput Card
                    html.Div(className="flex-1 bg-gray-800 bg-opacity-40 border border-white border-opacity-10 rounded-3xl p-6 backdrop-blur-xl shadow-xl flex flex-col", children=[
                        html.Div(className="flex justify-between items-center mb-6", children=[
                            html.Div(className="flex items-center gap-3", children=[
                                html.Div(html.I(className="fas fa-chart-line text-blue-500"), className="w-8 h-8 rounded-lg bg-blue-500 bg-opacity-10 flex items-center justify-center"),
                                html.Div([
                                    html.Span("THROUGHPUT", className="block text-xs font-bold text-gray-400 uppercase tracking-widest"),
                                    html.Span("REAL-TIME Gbits/sec", className="block text-xs font-bold text-gray-600 uppercase tracking-tighter"),
                                ])
                            ]),
                            html.Div([
                                html.Span(id="current-bw", children="0.00", className="text-3xl font-black text-blue-500 italic"),
                                html.Span(" Gbps", className="text-xs font-bold text-gray-600 uppercase not-italic ml-1")
                            ])
                        ]),
                        dcc.Graph(id="bw-chart", className="flex-1", figure=empty_graph(), config={'displayModeBar': False}),
                    ]),

                    # Small Stats Row
                    html.Div(className="grid grid-cols-2 gap-4", children=[
                        html.Div(className="p-4 bg-gray-800 bg-opacity-40 border border-white border-opacity-10 rounded-2xl", children=[
                            html.Span("JITTER", className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1"),
                            html.Div([
                                html.Span(id="stat-jitter", children="0.000", className="text-xl font-black text-amber-500"),
                                html.Span(" ms", className="text-xs font-bold text-gray-600 ml-1")
                            ])
                        ]),
                        html.Div(className="p-4 bg-gray-800 bg-opacity-40 border border-white border-opacity-10 rounded-2xl", children=[
                            html.Span("RETX", className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1"),
                            html.Div([
                                html.Span(id="stat-retx", children="0", className="text-xl font-black text-red-500"),
                                html.Span(" pkts", className="text-xs font-bold text-gray-600 ml-1")
                            ])
                        ])
                    ])
                ])
            ]),

            dcc.Interval(id="interval-update", interval=1500, n_intervals=0),
            dcc.Store(id="server-state", data={"running": False})
        ]
    )

    # ─── Callbacks ──────────────────────────────────────────────────────────────

    @dash_app.callback(
        Output("server-state", "data"),
        Output("status-badge", "className"),
        Output("status-dot", "className"),
        Output("status-text", "children"),
        Output("status-text", "className"),
        Input("btn-start", "n_clicks"),
        Input("btn-stop", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_server(n_start, n_stop):
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update
        
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if btn_id == "btn-start":
            IperfService.start_server()
            return {"running": True}, \
                   "flex items-center gap-3 px-4 py-2 border rounded-xl bg-gray-800 border-emerald-500 border-opacity-50 shadow-lg shadow-emerald-900/10", \
                   "w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.6)]", \
                   "SERVER ACTIVE", "text-xs font-bold text-emerald-500 uppercase tracking-widest"
        
        elif btn_id == "btn-stop":
            IperfService.stop_server()
            return {"running": False}, \
                   "flex items-center gap-3 px-4 py-2 border rounded-xl bg-gray-800 border-white border-opacity-10 shadow-inner", \
                   "w-3 h-3 rounded-full bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.6)]", \
                   "SERVER OFFLINE", "text-xs font-bold text-red-500 uppercase tracking-widest"

        return dash.no_update

    @dash_app.callback(
        Output("bw-chart", "figure"),
        Output("current-bw", "children"),
        Output("stat-jitter", "children"),
        Output("stat-retx", "children"),
        Output("log-output", "children"),
        Output("last-update", "children"),
        Input("interval-update", "n_intervals"),
        Input("btn-clear", "n_clicks"),
    )
    def update_metrics(n, n_clear):
        ctx = callback_context
        global log_lines
        
        if ctx.triggered and "btn-clear" in ctx.triggered[0]["prop_id"]:
            with lock:
                log_lines.clear()
            return dash.no_update

        # Leer logs y parsear data
        import os
        log_path = "/home/dtovar/bayblade/iperf/logs/iperf3_server.log"
        new_logs = ""
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
                new_logs = "".join(lines[-40:]) # Últimas 40 líneas
                
                # Intentar extraer bandwidth de la última línea formateada
                # Formato esperado: [2026-...] Test finalizado. Bandwidth: 10.70 Gbits/sec
                for line in reversed(lines):
                    if "Bandwidth:" in line:
                        try:
                            val_str = line.split("Bandwidth:")[1].split("Gbits/sec")[0].strip()
                            val = float(val_str)
                            ts = datetime.now().strftime("%H:%M:%S")
                            
                            with lock:
                                if not timestamps or timestamps[-1] != ts:
                                    timestamps.append(ts)
                                    recv_mbps.append(val)
                                    # Para demo, jitter y retx se extraen si están en JSON
                                    # Por ahora usaremos valores dummy o los extraeremos del JSON si existe
                                    if "JSON:" in line:
                                        data = json.loads(line.split("JSON:")[1])
                                        jitter_ms.append(data.get('end', {}).get('sum_received', {}).get('jitter_ms', 0))
                                        retransmits.append(data.get('end', {}).get('sum_sent', {}).get('retransmits', 0))
                            break
                        except:
                            pass

        # Construir Gráfica
        fig = go.Figure(layout=go.Layout(**{
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": dict(l=48, r=12, t=8, b=36),
            "hovermode": "x unified",
            "xaxis": dict(showgrid=False, color=MUTED, tickfont=dict(size=10)),
            "yaxis": dict(gridcolor="rgba(255,255,255,0.05)", color=MUTED, tickfont=dict(size=10))
        }))
        
        with lock:
            if timestamps:
                fig.add_trace(go.Scatter(
                    x=list(timestamps), y=list(recv_mbps),
                    name="Throughput",
                    line=dict(color="#2563eb", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(37,99,235,0.1)"
                ))

        last_bw = f"{recv_mbps[-1]:.2f}" if recv_mbps else "0.00"
        last_jit = f"{jitter_ms[-1]:.3f}" if jitter_ms else "0.000"
        last_retx = str(retransmits[-1]) if retransmits else "0"
        
        return fig, last_bw, last_jit, last_retx, \
               new_logs or "No activity recorded.", \
               f"LAST UPDATE: {datetime.now().strftime('%H:%M:%S')}"

    return dash_app
