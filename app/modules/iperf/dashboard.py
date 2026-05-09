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
        className="w-full h-full flex flex-col p-6 overflow-hidden bg-transparent",
        style={"fontFamily": "'Inter', sans-serif"},
        children=[
            # Header Title Section
            html.Div(className="mb-6 flex items-center justify-between", children=[
                html.Div(children=[
                    html.H1("Monitoreo de Red", className="text-2xl font-black text-primary uppercase tracking-tighter italic leading-none"),
                    html.P("iperf3 Orchestration & Analysis", className="text-[12px] text-primary/60 font-bold tracking-[0.3em] uppercase mt-1"),
                ]),
                html.Div(className="flex items-center gap-3", children=[
                    html.Div(id="status-badge", className="flex items-center gap-4 px-5 py-2.5 rounded-2xl bg-surface-container border border-panel-border shadow-xl shadow-primary/5", children=[
                        html.Div(id="status-dot", className="w-3 h-3 rounded-full bg-danger shadow-lg animate-pulse"),
                        html.Span(id="status-text", children="SERVIDOR FUERA DE LÍNEA", className="text-[11px] font-black text-danger uppercase tracking-widest")
                    ]),
                ])
            ]),

            # Controls Row
            html.Div(className="mb-8 flex items-center justify-between bg-panel-fill border border-panel-border p-5 rounded-[2rem] shadow-2xl shadow-primary/5", children=[
                html.Div(className="flex items-center gap-8 px-4", children=[
                    html.Div(className="flex flex-col", children=[
                        html.Span("Nodo Maestro", className="text-[10px] font-black text-label/30 uppercase tracking-widest"),
                        html.Span("Localhost:5201", className="text-sm font-bold text-label uppercase"),
                    ]),
                    html.Div(className="h-10 w-px bg-panel-border/50"),
                    html.Div(className="flex flex-col", children=[
                        html.Span("Protocolo", className="text-[10px] font-black text-label/30 uppercase tracking-widest"),
                        html.Span("TCP / UDP (Dinamico)", className="text-sm font-bold text-primary uppercase tracking-tighter"),
                    ]),
                ]),
                
                html.Div(className="flex gap-4", children=[
                    html.Button([
                        html.I(className="fas fa-play mr-2"), 
                        html.Span("Iniciar Servidor")
                    ], id="btn-start", className="nexus-btn nexus-btn-primary px-10 py-4 rounded-2xl shadow-2xl shadow-primary/30 group"),
                    
                    html.Button([
                        html.I(className="fas fa-stop mr-2"), 
                        html.Span("Detener")
                    ], id="btn-stop", className="nexus-btn nexus-btn-secondary border-rose-500/20 text-rose-500 hover:bg-rose-500/10 px-10 py-4 rounded-2xl shadow-2xl group"),
                ])
            ]),

            # Main Grid Layout (60/40 Split)
            html.Div(className="flex-grow grid grid-cols-1 lg:grid-cols-10 gap-6 overflow-hidden min-h-0", children=[
                
                # Left Column: Terminal (60%)
                html.Div(className="lg:col-span-6 flex flex-col min-h-0", children=[
                    html.Div(className="flex-1 bg-[#030712] border border-panel-border rounded-[2.5rem] overflow-hidden flex flex-col shadow-2xl relative group", children=[
                        # Terminal Header
                        html.Div(className="px-8 py-5 border-b border-white/5 bg-white/[0.02] flex items-center justify-between", children=[
                            html.Div(className="flex items-center gap-4", children=[
                                html.Div(className="flex gap-2", children=[
                                    html.Div(className="w-3 h-3 rounded-full bg-red-500/40"),
                                    html.Div(className="w-3 h-3 rounded-full bg-amber-500/40"),
                                    html.Div(className="w-3 h-3 rounded-full bg-emerald-500/40"),
                                ]),
                                html.Div(className="h-4 w-px bg-white/10 mx-2"),
                                html.Div(className="flex items-center gap-3", children=[
                                    html.I(className="fas fa-terminal text-primary text-xs"),
                                    html.Span("iperf3_runtime.log", className="text-[11px] font-black text-label/60 uppercase tracking-widest")
                                ]),
                            ]),
                            html.Button("Limpiar Consola", id="btn-clear", className="text-[10px] font-black text-label/30 hover:text-primary uppercase tracking-[0.2em] transition-all")
                        ]),
                        
                        # Terminal Body
                        html.Div(id="log-container", className="flex-1 p-8 font-mono text-[13px] overflow-y-auto custom-scrollbar bg-[radial-gradient(circle_at_50%_0%,rgba(37,99,235,0.08)_0%,transparent_100%)]", children=[
                            html.Pre(id="log-output", className="text-emerald-500/80 leading-relaxed whitespace-pre-wrap", children="Esperando inicialización de servicios...")
                        ]),

                        # Terminal Footer
                        html.Div(className="px-8 py-3 border-t border-white/5 bg-white/[0.01] flex justify-between items-center", children=[
                            html.P("nexus@master:~$ tail -f /var/log/iperf3.log", className="text-[10px] font-mono text-label/20 uppercase tracking-widest italic"),
                            html.P(id="last-update", children="Sincronización: --:--:--", className="text-[10px] font-mono text-label/20 uppercase tracking-widest")
                        ])
                    ])
                ]),

                # Right Column: Chart & Stats (40%)
                html.Div(className="lg:col-span-4 flex flex-col min-h-0 gap-6", children=[
                    # Chart Panel
                    html.Div(className="flex-grow bg-panel-fill border border-panel-border rounded-[2.5rem] p-8 shadow-2xl shadow-primary/5 flex flex-col relative overflow-hidden", children=[
                        html.Div(className="flex justify-between items-center mb-8 relative z-10", children=[
                            html.Div(className="flex items-center gap-4", children=[
                                html.Div(className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary shadow-inner", children=[
                                    html.I(className="fas fa-chart-line text-lg")
                                ]),
                                html.Div([
                                    html.Span("Throughput", className="block text-[11px] font-black text-label/60 uppercase tracking-widest leading-none"),
                                    html.Span("Análisis de Ancho de Banda", className="block text-[9px] font-black text-primary uppercase tracking-tighter mt-1"),
                                ])
                            ]),
                            html.Div(className="text-right", children=[
                                html.Span(id="current-bw", children="0.00", className="text-3xl font-black text-primary italic leading-none"),
                                html.Span(" Gbits/sec", className="text-[10px] font-black text-label/30 uppercase tracking-widest block mt-1")
                            ])
                        ]),
                        
                        dcc.Graph(id="bw-chart", className="flex-1", figure=empty_graph(), config={'displayModeBar': False}),
                    ]),

                    # Stats Panel
                    html.Div(className="bg-surface-container border border-panel-border rounded-[2.5rem] p-8 shadow-xl shadow-primary/5", children=[
                        html.Div(className="flex items-center gap-3 mb-6", children=[
                            html.Div(className="w-1.5 h-1.5 rounded-full bg-primary"),
                            html.H3("Métricas del Servidor", className="text-[11px] font-black text-label uppercase tracking-[0.2em]")
                        ]),
                        html.Div(className="grid grid-cols-2 gap-8", children=[
                            html.Div(className="group", children=[
                                html.Span("Jitter", className="block text-[9px] font-black text-label/30 uppercase tracking-widest mb-1"),
                                html.Div(className="flex items-center gap-2", children=[
                                    html.Span(id="stat-jitter", children="0.000", className="text-xl font-black text-label"),
                                    html.Span("ms", className="text-[10px] font-bold text-label/40 uppercase")
                                ])
                            ]),
                            html.Div(className="group text-right", children=[
                                html.Span("Retransmisiones", className="block text-[9px] font-black text-label/30 uppercase tracking-widest mb-1"),
                                html.Div(className="flex items-center justify-end gap-2", children=[
                                    html.Span(id="stat-retx", children="0", className="text-xl font-black text-danger"),
                                    html.Span("pkts", className="text-[10px] font-bold text-label/40 uppercase")
                                ])
                            ])
                        ]),
                        
                        html.Div(className="mt-8 pt-6 border-t border-panel-border/50 flex items-center justify-between", children=[
                            html.Div(className="flex -space-x-2", children=[
                                html.Div("N", className="w-8 h-8 rounded-full bg-primary/20 border-2 border-surface-container flex items-center justify-center text-[10px] font-black text-primary"),
                                html.Div("S", className="w-8 h-8 rounded-full bg-emerald-500/20 border-2 border-surface-container flex items-center justify-center text-[10px] font-black text-emerald-500"),
                            ]),
                            html.Span("Nexus Master Node v2.0", className="text-[10px] font-bold text-label/40 uppercase tracking-widest italic")
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
                   "flex items-center gap-4 px-5 py-2.5 rounded-2xl bg-surface-container border border-success/30 shadow-xl shadow-success/10", \
                   "w-3 h-3 rounded-full bg-success shadow-[0_0_15px_rgba(var(--color-success),0.5)] animate-pulse", \
                   "SERVIDOR ACTIVO", "text-[11px] font-black text-success uppercase tracking-widest"
        
        elif btn_id == "btn-stop":
            IperfService.stop_server()
            return {"running": False}, \
                   "flex items-center gap-4 px-5 py-2.5 rounded-2xl bg-surface-container border border-panel-border shadow-xl shadow-primary/5", \
                   "w-3 h-3 rounded-full bg-danger shadow-[0_0_15px_rgba(var(--color-danger),0.5)]", \
                   "SERVIDOR FUERA DE LÍNEA", "text-[11px] font-black text-danger uppercase tracking-widest"

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
                                    if "JSON:" in line:
                                        data = json.loads(line.split("JSON:")[1])
                                        jitter_ms.append(data.get('end', {}).get('sum_received', {}).get('jitter_ms', 0))
                                        retransmits.append(data.get('end', {}).get('sum_sent', {}).get('retransmits', 0))
                            break
                        except:
                            pass

        # Construir Gráfica
        fig = go.Figure()
        
        with lock:
            if timestamps:
                fig.add_trace(go.Scatter(
                    x=list(timestamps), y=list(recv_mbps),
                    name="Throughput",
                    line=dict(color="#2563eb", width=4, shape='spline', smoothing=1.3),
                    fill="tozeroy",
                    fillcolor="rgba(37,99,235,0.08)",
                    mode='lines',
                    hoverinfo='y+name',
                ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=48, r=12, t=8, b=36),
            hovermode="x unified",
            xaxis=dict(
                showgrid=False, 
                color="rgba(255,255,255,0.2)", 
                tickfont=dict(size=10, weight='bold'),
                zeroline=False
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.03)", 
                color="rgba(255,255,255,0.2)", 
                tickfont=dict(size=10, weight='bold'),
                zeroline=False,
                side='left'
            ),
            showlegend=False
        )
        
        last_bw = f"{recv_mbps[-1]:.2f}" if recv_mbps else "0.00"
        last_jit = f"{jitter_ms[-1]:.3f}" if jitter_ms else "0.000"
        last_retx = str(retransmits[-1]) if retransmits else "0"
        
        return fig, last_bw, last_jit, last_retx, \
               new_logs or "No se ha registrado actividad.", \
               f"Sincronización: {datetime.now().strftime('%H:%M:%S')}"

    return dash_app
