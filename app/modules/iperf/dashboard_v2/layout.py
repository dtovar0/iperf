from dash import html, dcc

def get_main_frame(content):
    # Solo devolvemos el contenedor de contenido. 
    # El TopBar y Sidebar ya vienen del base.html de Flask.
    return html.Div(id="dash-content-container", className="flex-1 min-h-0 flex flex-col p-8 relative overflow-hidden", children=[
        *content,

        dcc.Location(id='url', refresh=False),
        dcc.Interval(id="interval-update", interval=2000, n_intervals=0),
        dcc.Store(id="ui-state", data={"active_tab": "server", "last_session_id": None}),
        # Store para el estado del servidor (leído por JS externo para actualizar la TopBar de Flask)
        dcc.Store(id="srv-status-store", data={"status": "OFFLINE", "msg": "Puerto 5201 Disponible"})
    ])
