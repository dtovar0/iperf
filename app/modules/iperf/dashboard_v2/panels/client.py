from dash import html, dcc


def _chart_card(title, icon_cls, icon_color, stat_id, stat_unit, graph_id, accent_color):
    return html.Div(className="bg-surface-container border border-white/5 rounded-3xl overflow-hidden mb-4", children=[
        html.Div(className="p-6 border-b border-white/5 flex justify-between items-center", children=[
            html.Div(className="flex items-center gap-3", children=[
                html.I(className=f"{icon_cls} text-sm", style={"color": accent_color}),
                html.Span(title, className="text-[10px] font-black uppercase tracking-[0.2em] text-label/60"),
            ]),
            html.Div(className="flex items-baseline gap-1", children=[
                html.Span(id=stat_id, className="text-xl font-black italic", style={"color": accent_color}, children="0.00"),
                html.Span(stat_unit, className="text-[9px] font-black text-label/20"),
            ])
        ]),
        html.Div(className="p-4", style={"height": "250px"}, children=[
            dcc.Graph(
                id=graph_id,
                style={"height": "100%", "width": "100%"},
                config={"displayModeBar": False, "responsive": True}
            )
        ])
    ])


def get_client_panel():
    return html.Div(id="panel-client", className="iperf-panel hidden", children=[
        # FILA 1: CONTROLES
        html.Div(className="flex items-center gap-4 p-4 bg-surface-container/50 rounded-2xl mb-6", children=[
            html.Button(
                [html.I(className="fas fa-satellite-dish mr-2"), "EJECUTAR TEST"],
                id="btn-cli-start", className="bg-primary text-white px-6 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all"
            ),
            html.Div(className="w-px h-8 bg-white/5 mx-2"),
            html.Div([
                html.Label("HOST", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Input(id="cli-host", type="text", value="127.0.0.1", className="bg-transparent border-none text-sm font-black text-primary w-32 outline-none")
            ]),
            html.Div([
                html.Label("PUERTO", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Input(id="cli-port", type="number", value=5201, className="bg-transparent border-none text-sm font-black text-primary w-20 outline-none")
            ]),
            html.Div([
                html.Label("DURACIÓN", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Input(id="cli-duration", type="number", value=10, className="bg-transparent border-none text-sm font-black text-primary w-16 outline-none")
            ]),
            html.Div([
                html.Label("STREAMS (-P)", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Input(id="cli-parallel", type="number", value=1, min=1, max=128, className="bg-transparent border-none text-sm font-black text-primary w-16 outline-none")
            ]),
            html.Div([
                html.Label("BITRATE (-b)", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Input(id="cli-bitrate", type="text", placeholder="200M", className="bg-transparent border-none text-sm font-black text-primary w-20 outline-none")
            ]),
            html.Div([
                html.Label("PROTOCOLO", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Dropdown(
                    id="cli-proto",
                    options=[{"label": "TCP", "value": "tcp"}, {"label": "UDP", "value": "udp"}],
                    value="tcp",
                    className="nexus-dropdown-premium w-24",
                    clearable=False,
                ),
            ]),
            html.Div(className="flex-1"),
            html.Div(id="cli-status-card", className="flex items-center gap-3 px-4 py-2 rounded-xl border border-white/5 bg-white/5", children=[
                html.Div(className="w-2 h-2 rounded-full bg-slate-500"),
                html.Span(id="cli-status-label", children="STANDBY", className="text-[10px] font-black uppercase tracking-widest")
            ])
        ]),

        # FILA 2: KPI GRID
        html.Div(className="grid grid-cols-2 gap-4 mb-6", children=[
            html.Div(className="bg-surface-container border border-white/5 rounded-2xl p-6 text-center", children=[
                html.P("CURRENT THROUGHPUT", className="text-[9px] font-black text-label/30 tracking-widest mb-2"),
                html.H2(id="cli-current-bw", children="0.00", className="text-3xl font-black italic text-primary"),
                html.P("Gbps", className="text-[8px] font-black text-label/10 uppercase mt-1"),
            ]),
            html.Div(className="bg-surface-container border border-white/5 rounded-2xl p-6 text-center", children=[
                html.P("LATENCIA (JITTER)", className="text-[9px] font-black text-label/30 tracking-widest mb-2"),
                html.H2(id="cli-stat-jitter", children="0.000", className="text-3xl font-black italic text-amber-400"),
                html.P("ms", className="text-[8px] font-black text-label/10 uppercase mt-1"),
            ]),
        ]),

        # FILA 3: HEADER
        html.Header(className="nx-section-header", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("ANÁLISIS DE CLIENTE", className="nx-section-header__label"),
            ]),
            html.Span(id="cli-realtime-sub", children="ESPERANDO ACTIVACIÓN", className="nx-section-header__sub"),
        ]),

        # FILA 4: CHARTS & LOG
        html.Div(className="grid grid-cols-12 gap-6", children=[
            html.Div(className="col-span-7", children=[
                _chart_card("Estabilidad de Conexión", "fas fa-chart-line", "#00d4ff", "cli-current-bw-chart", "Gbps", "cli-bw-chart", "#00d4ff"),
                _chart_card("Variación de Latencia", "fas fa-wave-square", "#ffd166", "cli-stat-jitter-chart", "ms", "cli-jitter-chart", "#ffd166"),
            ]),
            html.Div(className="col-span-5", children=[
                html.Div(className="bg-[#020617] border border-white/5 rounded-3xl h-full flex flex-col overflow-hidden shadow-2xl", children=[
                    html.Div(className="p-6 border-b border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Span("TELEMETRÍA DE CLIENTE", className="text-[10px] font-black text-label/60 tracking-widest"),
                        html.Button(html.I(className="fas fa-trash-alt text-xs"), id="btn-cli-clear", className="text-label/20 hover:text-rose-500 transition-colors")
                    ]),
                    html.Div(id="cli-log-container", className="flex-1 p-6 overflow-y-auto font-mono text-[11px] custom-scrollbar", children=[
                        html.Pre(id="cli-log-output", className="text-emerald-500/60", children="[NEXUS] Esperando datos...")
                    ]),
                    html.Div(className="p-4 border-t border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Span("iperf3 engine v3.16", className="text-[8px] font-black text-label/20"),
                        html.Span(id="cli-last-update", className="text-[8px] font-black text-primary/40", children="IDLE")
                    ])
                ])
            ])
        ])
    ])
