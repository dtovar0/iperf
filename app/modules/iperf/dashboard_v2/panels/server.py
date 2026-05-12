from dash import html, dcc
from app.modules.iperf.dashboard_v2.panels.components import chart_card
def get_server_panel():
    from app.modules.iperf.models import IperfServerConfig
    # Fetch active servers from DB
    try:
        db_servers = IperfServerConfig.query.filter_by(is_active=True).order_by(IperfServerConfig.name).all()
        server_options = [{"label": f"{s.name} ({s.host})", "value": s.host} for s in db_servers]
    except Exception:
        server_options = []

    # Default options
    default_options = [
        {"label": "0.0.0.0 (ANY)", "value": "0.0.0.0"},
        {"label": "127.0.0.1 (LOCAL)", "value": "127.0.0.1"},
    ]
    
    final_options = default_options + server_options

    return html.Div(id="panel-server", className="iperf-panel h-full", children=[
        # FILA 0: HEADER CONFIGURACIÓN
        html.Header(className="flex-shrink-0 nx-section-header !pb-2", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("CONFIGURACIÓN DEL SERVIDOR", className="nx-section-header__label"),
            ]),
        ]),

        # FILA 1: CONTROLES
        html.Div(className="flex-shrink-0 flex items-center gap-4 p-4 bg-panel-fill border border-panel-border rounded-panel shadow-sm", children=[
            # Puerto
            html.Div(className="flex items-center gap-2", children=[
                html.Label("PUERTO", className="text-2xs font-black text-label/40 tracking-widest"),
                dcc.Input(
                    id="srv-port",
                    type="number",
                    value=5201,
                    className="iperf-input w-20"
                )
            ]),

            # Interfaz (SELECT LIGADO A DB)
            html.Div(className="flex items-center gap-2 ml-4", children=[
                html.Label("SERVER", className="text-2xs font-black text-label/40 tracking-widest"),
                dcc.Dropdown(
                    id="srv-interface",
                    options=final_options,
                    value="0.0.0.0",
                    clearable=False,
                    searchable=True,
                    className="iperf-control-bar__dropdown !w-48"
                )
            ]),

            html.Div(className="w-px h-8 bg-panel-border/30 mx-2"),

            # Acción
            html.Button(
                [html.I(id="srv-toggle-icon", className="fas fa-play mr-2"), html.Span(id="srv-toggle-text", children="INICIAR")],
                id="btn-srv-toggle", className="iperf-btn-action"
            ),

            html.Div(className="flex-1"),
            
            # Estado
            html.Div(id="srv-status-card", className="flex items-center gap-3 px-4 py-2 rounded-base border border-panel-border/30 bg-surface-container/30", children=[
                html.Div(id="srv-status-dot", className="w-2 h-2 rounded-full bg-slate-500"),
                html.Span(id="srv-status-label", children="STANDBY", className="text-2xs font-black uppercase tracking-widest")
            ])
        ]),

        # FILA 2: HEADER ANÁLISIS
        html.Header(className="flex-shrink-0 nx-section-header !pb-2", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("ANÁLISIS DEL SERVIDOR", className="nx-section-header__label"),
            ]),
        ]),

        # FILA 3: CONTENIDO PRINCIPAL (70/30) - Responsivo
        html.Div(className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch", children=[
            # COLUMNA IZQUIERDA: GRÁFICAS (70%)
            html.Div(className="lg:col-span-8 flex flex-col gap-6 h-full min-h-0 pr-2", children=[
                chart_card("Estabilidad de Ancho de Banda", "fas fa-chart-line", "rgb(var(--color-accent-sky))", "current-bw-chart", "Mbps", "bw-chart"),
                chart_card("Variación de Latencia", "fas fa-wave-square", "rgb(var(--color-accent-peach))", "stat-jitter-chart", "ms", "jitter-chart"),
            ]),

            # COLUMNA DERECHA: LOGS (30%)
            html.Div(className="lg:col-span-4 h-full min-h-0", children=[
                html.Div(className="bg-slate-950 border border-panel-border rounded-panel h-full flex flex-col overflow-hidden shadow-2xl min-h-[300px]", children=[
                    html.Div(className="flex-shrink-0 p-6 border-b border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Div(className="flex items-center gap-3", children=[
                            html.I(className="fas fa-terminal text-slate-400 text-sm"),
                            html.Span("TELEMETRÍA EN VIVO", className="text-2xs font-black text-slate-200 tracking-widest"),
                        ]),
                        html.I(className="fas fa-bolt text-primary text-2xs animate-pulse")
                    ]),
                    html.Div(id="log-container", className="flex-1 p-6 overflow-y-auto font-mono text-sm custom-scrollbar bg-black/20", children=[
                        html.Pre(id="log-output", className="text-emerald-400 leading-relaxed", children="[NEXUS] Iniciando telemetría...")
                    ]),
                    html.Div(className="flex-shrink-0 p-4 border-t border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Span("iperf3 engine v3.16", className="text-2xs font-black text-slate-400"),
                        html.Span(id="last-update", children="--:--:--", className="iperf-last-update")
                    ])
                ])
            ])
        ])
    ])
