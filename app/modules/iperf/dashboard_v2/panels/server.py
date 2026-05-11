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


def get_server_panel():
    return html.Div(id="panel-server", className="iperf-panel", children=[
        # FILA 1: CONTROLES
        html.Div(className="flex items-center gap-4 p-4 bg-surface-container/50 rounded-2xl mb-6", children=[
            html.Button(
                [html.I(id="srv-toggle-icon", className="fas fa-play mr-2"), html.Span(id="srv-toggle-text", children="INICIAR")],
                id="btn-srv-toggle", className="bg-primary text-white px-8 py-3 rounded-xl font-black text-xs tracking-widest hover:scale-105 transition-all flex items-center"
            ),
            html.Div(className="w-px h-8 bg-white/5 mx-2"),
            html.Div([
                html.Label("PUERTO", className="block text-[8px] font-black text-label/40 mb-1"),
                dcc.Input(id="srv-port", type="number", value=5201, className="bg-transparent border-none text-lg font-black text-primary w-20 outline-none")
            ]),
            html.Div(className="flex-1"),
            html.Div(id="srv-status-card", className="flex items-center gap-3 px-4 py-2 rounded-xl border border-white/5 bg-white/5", children=[
                html.Div(id="srv-status-dot", className="w-2 h-2 rounded-full bg-slate-500"),
                html.Span(id="srv-status-label", children="STANDBY", className="text-[10px] font-black uppercase tracking-widest")
            ])
        ]),

        # FILA 2: CONTENIDO PRINCIPAL (70/30)
        html.Div(className="grid grid-cols-12 gap-6 items-stretch", children=[
            # COLUMNA IZQUIERDA: GRÁFICAS (70%)
            html.Div(className="col-span-8 space-y-6", children=[
                _chart_card("Estabilidad de Ancho de Banda", "fas fa-chart-line", "#00d4ff", "current-bw-chart", "Mbps", "bw-chart", "#00d4ff"),
                _chart_card("Variación de Latencia", "fas fa-wave-square", "#ffd166", "stat-jitter-chart", "ms", "jitter-chart", "#ffd166"),
                _chart_card("Retransmisiones de Red", "fas fa-redo-alt", "#ff6b6b", "stat-retx-chart", "pkts", "retx-chart", "#ff6b6b"),
            ]),

            # COLUMNA DERECHA: KPIs + LOGS (30%)
            html.Div(className="col-span-4 flex flex-col gap-6", children=[
                # KPI GRID (3 en una sola fila)
                html.Div(className="grid grid-cols-3 gap-2", children=[
                    html.Div(className="bg-surface-container border border-white/5 rounded-2xl p-4 text-center", children=[
                        html.P("BW", className="text-[7px] font-black text-label/30 tracking-widest mb-1"),
                        html.H2(id="current-bw", children="0.00", className="text-xl font-black italic text-primary"),
                        html.P("Mbps", className="text-[6px] font-black text-label/10 uppercase"),
                    ]),
                    html.Div(className="bg-surface-container border border-white/5 rounded-2xl p-4 text-center", children=[
                        html.P("JITTER", className="text-[7px] font-black text-label/30 tracking-widest mb-1"),
                        html.H2(id="stat-jitter", children="0.000", className="text-xl font-black italic text-amber-400"),
                        html.P("ms", className="text-[6px] font-black text-label/10 uppercase"),
                    ]),
                    html.Div(className="bg-surface-container border border-white/5 rounded-2xl p-4 text-center", children=[
                        html.P("RETX", className="text-[7px] font-black text-label/30 tracking-widest mb-1"),
                        html.H2(id="stat-retx", children="0", className="text-xl font-black italic text-rose-500"),
                        html.P("pkts", className="text-[6px] font-black text-label/10 uppercase"),
                    ]),
                ]),

                # LOGS
                html.Div(className="bg-[#020617] border border-white/5 rounded-3xl flex-1 flex flex-col overflow-hidden shadow-2xl min-h-[400px]", children=[
                    html.Div(className="p-6 border-b border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Span("TELEMETRÍA EN VIVO", className="text-[10px] font-black text-label/60 tracking-widest"),
                        html.I(className="fas fa-terminal text-primary text-xs")
                    ]),
                    html.Div(id="log-container", className="flex-1 p-6 overflow-y-auto font-mono text-[11px] custom-scrollbar", children=[
                        html.Pre(id="log-output", className="text-emerald-500/60", children="[NEXUS] Esperando datos...")
                    ]),
                    html.Div(className="p-4 border-t border-white/5 bg-white/5 flex justify-between items-center", children=[
                        html.Span("iperf3 engine v3.16", className="text-[8px] font-black text-label/20"),
                        html.Span(id="last-update", className="text-[8px] font-black text-primary/40", children="IDLE")
                    ])
                ])
            ])
        ])
    ])
