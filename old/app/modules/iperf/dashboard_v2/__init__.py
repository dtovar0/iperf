import dash
from dash import html, dcc
import plotly.graph_objs as go
from collections import deque
import threading
from datetime import datetime

from app.modules.iperf.dashboard_v2.layout import get_main_frame
from app.modules.iperf.dashboard_v2.panels.server import get_server_panel
from app.modules.iperf.dashboard_v2.panels.client import get_client_panel
from app.modules.iperf.dashboard_v2.panels.history import get_history_panel
from app.modules.iperf.dashboard_v2.callbacks import register_callbacks

# Estructuras de datos globales
MAX_POINTS = 60
timestamps = deque(maxlen=MAX_POINTS)
recv_mbps = deque(maxlen=MAX_POINTS)
jitter_ms = deque(maxlen=MAX_POINTS)
retransmits = deque(maxlen=MAX_POINTS)
log_lines = deque(maxlen=100)
lock = threading.Lock()

def empty_graph(small=False, color="#2563eb"):
    m = dict(l=44, r=8, t=4, b=32) if small else dict(l=48, r=12, t=8, b=36)
    fs = 9 if small else 10
    MUTED = "#64748b"
    BORDER = "rgba(255,255,255,0.05)"
    return {"data": [], "layout": go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=m,
        xaxis=dict(showgrid=False, color=MUTED, tickfont=dict(size=fs)),
        yaxis=dict(gridcolor=BORDER, color=MUTED, tickfont=dict(size=fs), zeroline=False),
    )}

from flask import render_template

def init_dashboard(server):
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/iperf/',
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
    )

    def interpolate_index(**kwargs):
        return render_template('iperf/dash_base.html', is_dash_iperf=True, **kwargs)
    
    dash_app.interpolate_index = interpolate_index

    # === LAYOUT SIMPLIFICADO (Solo el contenido) ===
    dash_app.layout = get_main_frame(
        html.Div([
            get_server_panel(),
            get_client_panel(),
            get_history_panel(),
            
            # Modal de Resumen (Global)
            html.Div(id="modal-summary", className="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md", children=[
                html.Div(className="bg-panel-fill border border-panel-border w-[500px] rounded-[3rem] p-12 shadow-[0_0_50px_rgba(37,99,235,0.2)] text-center", children=[
                    html.Div(className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-8", children=[
                        html.I(className="fas fa-check-circle text-4xl text-primary")
                    ]),
                    html.H2("TEST COMPLETADO", className="text-2xl font-black text-text uppercase mb-4"),
                    html.P(id="modal-msg", className="text-label/40 text-sm mb-10"),
                        html.Div(className="flex flex-col gap-4", children=[
                            html.Button("GUARDAR EN BASE DE DATOS", id="btn-save-db", className="bg-emerald-500 text-white py-4 rounded-2xl font-black uppercase tracking-widest hover:bg-emerald-600 transition-all"),
                            html.A("DESCARGAR REPORTE PDF", id="modal-download-link", href="#", target="_blank", className="bg-primary text-white py-4 rounded-2xl font-black text-center uppercase tracking-widest hover:bg-primary/80 transition-all"),
                            html.Button("DESCARTAR Y CERRAR", id="btn-modal-close", className="text-label/40 text-xs font-black uppercase tracking-widest hover:text-text transition-all")
                        ])
                ])
            ]),
        ])
    )

    register_callbacks(dash_app, lock, timestamps, recv_mbps, jitter_ms, retransmits, log_lines, empty_graph)

    return dash_app
