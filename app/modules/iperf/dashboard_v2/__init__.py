import dash
from dash import html, dcc
import plotly.graph_objs as go
from flask import render_template, request

# Importar el estado compartido para evitar duplicados
from app.modules.iperf.dashboard_v2.state import timestamps, recv_mbps, jitter_ms, retransmits, log_lines, lock

def empty_graph(small=False, color="#2563eb"):
    m = dict(l=44, r=8, t=4, b=32) if small else dict(l=48, r=12, t=8, b=36)
    fs = 9 if small else 10
    MUTED = "#64748b"
    BORDER = "rgba(255,255,255,0.05)"
    return go.Figure(data=[], layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=m,
        xaxis=dict(showgrid=False, color=MUTED, tickfont=dict(size=fs)),
        yaxis=dict(gridcolor=BORDER, color=MUTED, tickfont=dict(size=fs), zeroline=False),
    ))

def init_dashboard(server):
    import os
    # Assets folder está en la raíz del proyecto, no relativo al módulo
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    assets_path = os.path.join(project_root, 'assets')
    
    # Inicialización limpia (siguiendo test/app.py)
    dash_app = dash.Dash(
        __name__,
        server=server,
        routes_pathname_prefix='/iperf/',
        # Forzar rutas relativas para evitar problemas de localhost/127.0.0.1
        requests_pathname_prefix='/iperf/',
        assets_folder=assets_path,
        update_title=None,
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ]
    )

    def interpolate_index(**kwargs):
        return render_template('iperf/dash_base.html', is_dash_iperf=True, **kwargs)
    
    dash_app.interpolate_index = interpolate_index

    def serve_layout():
        # Importación diferida de paneles para evitar circularidad
        from app.modules.iperf.dashboard_v2.layout import get_main_frame
        from app.modules.iperf.dashboard_v2.panels.server import get_server_panel
        from app.modules.iperf.dashboard_v2.panels.client import get_client_panel
        from app.modules.iperf.dashboard_v2.panels.history import get_history_panel

        path = request.path
        srv_class = "iperf-panel hidden"
        cli_class = "iperf-panel hidden"
        his_class = "iperf-panel hidden"
        
        if "/client" in path:
            cli_class = "iperf-panel"
        elif "/history" in path:
            his_class = "iperf-panel"
        else:
            srv_class = "iperf-panel"

        srv_panel = get_server_panel()
        srv_panel.className = srv_class
        cli_panel = get_client_panel()
        cli_panel.className = cli_class
        his_panel = get_history_panel()
        his_panel.className = his_class

        return get_main_frame([
            srv_panel,
            cli_panel,
            his_panel,
            # Modal (Sincronizado con test/app.py)
            html.Div(id="modal-summary", className="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md", children=[
                html.Div(className="bg-panel-fill border border-panel-border w-[500px] rounded-[3rem] p-12 text-center", children=[
                    html.I(className="fas fa-check-circle text-6xl text-emerald-500 mb-6"),
                    html.H2("SESIÓN FINALIZADA", className="text-2xl font-black text-text uppercase mb-4"),
                    html.P(id="modal-msg", className="text-label/60 text-sm mb-10"),
                    html.Div(className="flex flex-col gap-3", children=[
                        html.A("VER REPORTE DETALLADO", id="modal-download-link", href="#", className="bg-primary text-white py-4 rounded-2xl font-black uppercase tracking-widest"),
                        html.Button("CERRAR", id="btn-modal-close", className="text-label/40 text-xs font-black uppercase")
                    ])
                ])
            ]),
        ])

    dash_app.layout = serve_layout

    # Importación diferida de callbacks (CRÍTICO para evitar circularidad)
    from app.modules.iperf.dashboard_v2.callbacks import register_callbacks
    register_callbacks(dash_app, lock, timestamps, recv_mbps, jitter_ms, retransmits, log_lines, empty_graph)

    return dash_app
