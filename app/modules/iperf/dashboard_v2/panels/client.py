from dash import html, dcc
from app.modules.iperf.dashboard_v2.panels.components import chart_card


def get_client_panel():
    return html.Div(id="panel-client", className="iperf-panel hidden h-full", children=[
        # FILA 0: HEADER CONFIGURACIÓN
        html.Header(className="flex-shrink-0 nx-section-header !pb-2", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("CONFIGURACIÓN DEL CLIENTE", className="nx-section-header__label"),
            ]),
        ]),

        # FILA 1: CONTROLES PRINCIPALES (Audit #1 — Línea principal limpia)
        html.Div(className="flex-shrink-0 flex items-center gap-4 p-4 bg-panel-fill border border-panel-border rounded-panel shadow-sm", children=[
            # Host
            html.Div(className="flex items-center gap-2", children=[
                html.Label("HOST", className="text-2xs font-black text-label/40 tracking-widest"),
                dcc.Input(id="cli-host", type="text", value="127.0.0.1", 
                          className="iperf-input w-32")
            ]),

            # Puerto
            html.Div(className="flex items-center gap-2", children=[
                html.Label("PUERTO", className="text-2xs font-black text-label/40 tracking-widest"),
                dcc.Input(id="cli-port", type="number", value=5201, 
                          className="iperf-input w-20")
            ]),

            # Protocolo (Custom Premium Toggle)
            html.Div(className="flex items-center gap-2", children=[
                html.Label("PROTO", className="text-2xs font-black text-label/40 tracking-widest"),
                html.Div(className="proto-toggle-group", children=[
                    html.Button("TCP", id="btn-proto-tcp", n_clicks=0, className="proto-toggle-btn"),
                    html.Button("UDP", id="btn-proto-udp", n_clicks=0, className="proto-toggle-btn"),
                ]),
                # Input oculto para mantener compatibilidad con callbacks existentes
                dcc.Input(id="cli-proto", value="tcp", className="hidden")
            ]),

            html.Div(className="w-px h-8 bg-panel-border/30 mx-1"),

            # Parámetros Avanzados (Audit #1 — Agrupados)
            html.Div(className="flex items-center gap-3 px-3 py-1 rounded-lg bg-white/[0.02] border border-white/5", children=[
                html.Div(className="flex items-center gap-2", children=[
                    html.Label("TIME", className="text-2xs font-black text-label/40 tracking-widest"),
                    dcc.Input(id="cli-duration", type="number", value=10, 
                              className="iperf-input w-16")
                ]),
                html.Div(className="flex items-center gap-2", children=[
                    html.Label("FLUJOS", className="text-2xs font-black text-label/40 tracking-widest"),
                    dcc.Input(id="cli-parallel", type="number", value=1, min=1, max=128, 
                              className="iperf-input w-14")
                ]),
                html.Div(className="flex items-center gap-2", children=[
                    html.Label("RATE", className="text-2xs font-black text-label/40 tracking-widest"),
                    dcc.Input(id="cli-bitrate", type="text", placeholder="MAX", 
                              className="iperf-input w-20")
                ]),
            ]),

            html.Div(className="w-px h-8 bg-panel-border/30 mx-1"),

            # Acción
            html.Button(
                [html.I(id="cli-toggle-icon", className="fas fa-play mr-2"), html.Span(id="cli-toggle-text", children="INICIAR")],
                id="btn-cli-toggle", className="iperf-btn-action"
            ),

            html.Div(className="flex-1"),
            
            # Estado (Audit #3 — dot con ID dinámico)
            html.Div(id="cli-status-card", className="flex items-center gap-3 px-4 py-2 rounded-xl border border-panel-border/30 bg-surface-container/30", children=[
                html.Div(id="cli-status-dot", className="w-2 h-2 rounded-full bg-slate-500"),
                html.Span(id="cli-status-label", children="STANDBY", className="text-2xs font-black uppercase tracking-widest")
            ])
        ]),

        # FILA 2: HEADER ANÁLISIS
        html.Header(className="flex-shrink-0 nx-section-header !pb-2", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("ANÁLISIS DE CLIENTE", className="nx-section-header__label"),
            ]),
        ]),

        # FILA 3: CHARTS & LOG - Responsivo 70/30
        html.Div(className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch", children=[
            # COLUMNA IZQUIERDA: GRÁFICAS (70%)
            html.Div(className="lg:col-span-8 flex flex-col gap-6 h-full min-h-0 pr-2", children=[
                chart_card("Estabilidad de Conexión", "fas fa-chart-line", "rgb(var(--color-accent-sky))", "cli-current-bw-chart", "Gbps", "cli-bw-chart"),
                chart_card("Variación de Latencia", "fas fa-wave-square", "rgb(var(--color-accent-peach))", "cli-stat-jitter-chart", "ms", "cli-jitter-chart"),
            ]),

            # COLUMNA DERECHA: LOGS (30%)
            html.Div(className="lg:col-span-4 h-full min-h-0", children=[
                html.Div(className="bg-slate-950 border border-panel-border rounded-panel h-full flex flex-col overflow-hidden shadow-2xl min-h-[300px]", children=[
                    html.Div(className="flex-shrink-0 p-6 border-b border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Div(className="flex items-center gap-3", children=[
                            html.I(className="fas fa-terminal text-slate-400 text-sm"),
                            html.Span("TELEMETRÍA EN VIVO", className="text-2xs font-black text-slate-200 tracking-widest"),
                        ]),
                        html.Div(className="flex items-center gap-4", children=[
                            html.Button(html.I(className="fas fa-trash-alt text-xs"), id="btn-cli-clear", className="text-label/20 hover:text-rose-500 transition-colors"),
                            html.I(className="fas fa-bolt text-primary text-2xs animate-pulse")
                        ])
                    ]),
                    html.Div(id="cli-log-container", className="flex-1 p-6 overflow-y-auto font-mono text-sm custom-scrollbar bg-black/20", children=[
                        html.Pre(id="cli-log-output", className="text-emerald-400 leading-relaxed", children="[NEXUS] Iniciando telemetría...")
                    ]),
                    # Footer con timestamp visible (Audit #5)
                    html.Div(className="flex-shrink-0 p-4 border-t border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Span("iperf3 engine v3.16", className="text-2xs font-black text-slate-400"),
                        html.Span(id="cli-last-update", children="--:--:--", className="iperf-last-update")
                    ])
                ])
            ])
        ])
    ])
