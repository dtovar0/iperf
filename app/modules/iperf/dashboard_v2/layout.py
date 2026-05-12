from dash import html, dcc

def get_main_frame(content):
    # Solo devolvemos el contenedor de contenido. 
    # El TopBar y Sidebar ya vienen del base.html de Flask.
    return html.Div(id="dash-content-container", className="flex-1 min-h-0 flex flex-col p-8 relative overflow-hidden h-full", children=[
        *content,

        dcc.Location(id='url', refresh=False),
        dcc.Interval(id="interval-update", interval=1000, n_intervals=0),
        dcc.Store(id="ui-state", data={"active_tab": "server", "last_session_id": None}),
        # Store para el estado del servidor (leído por JS externo para actualizar la TopBar de Flask)
        dcc.Store(id="srv-status-store", data={"status": "OFFLINE", "msg": "Puerto 5201 Disponible"}),
        
        # Tracking de estados para notificaciones toast
        dcc.Store(id="status-sync-store", data={"server": None, "client": None}),

        # Contenedor para notificaciones Toast Premium
        html.Div(id="toast-container", className="fixed bottom-8 right-8 z-[9999] flex flex-col gap-3"),
        dcc.Store(id="toast-trigger", data=None)
    ])
