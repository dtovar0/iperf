from dash import html, dcc

def get_client_panel():
    return html.Div(id="panel-client", className="flex-1 flex flex-col min-h-0 animate-in fade-in duration-500", children=[
        
        # 1. CABECERA: CONFIGURACIÓN (1:1)
        html.Header(className="nx-section-header", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("CLIENT CONFIGURATION", className="nx-section-header__label"),
            ]),
            html.Span("SÍNTESIS DE PARÁMETROS DE DIAGNÓSTICO", className="nx-section-header__sub")
        ]),

        # CONTENEDOR DE CONFIGURACIÓN (Estilo Analytic Card 1:1)
        html.Div(className="dashboard-analytics-wrap !pb-0", children=[
            html.Div(className="bg-panel-fill border border-panel-border rounded-xl p-8 shadow-sm flex flex-col gap-8", children=[
                
                # GRID DE INPUTS (Siguiendo la densidad visual de Nexus)
                html.Div(className="grid grid-cols-12 gap-8", children=[
                    # HOST
                    html.Div(className="col-span-4 space-y-3", children=[
                        html.Label("HOST DESTINO", className="text-[10px] font-black text-label/40 uppercase tracking-widest px-1"),
                        dcc.Input(
                            id="cli-host", type="text", value="127.0.0.1",
                            className="w-full bg-surface-container/30 border border-panel-border rounded-xl px-6 py-4 text-white font-black text-lg focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all outline-none"
                        )
                    ]),
                    # PUERTO
                    html.Div(className="col-span-2 space-y-3", children=[
                        html.Label("GATEWAY PORT", className="text-[10px] font-black text-label/40 uppercase tracking-widest px-1"),
                        dcc.Input(
                            id="cli-port", type="number", value=5201,
                            className="w-full bg-surface-container/30 border border-panel-border rounded-xl px-6 py-4 text-white font-black text-lg focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all outline-none"
                        )
                    ]),
                    # DURACIÓN
                    html.Div(className="col-span-2 space-y-3", children=[
                        html.Label("DURATION (SEC)", className="text-[10px] font-black text-label/40 uppercase tracking-widest px-1"),
                        dcc.Input(
                            id="cli-duration", type="number", value=10,
                            className="w-full bg-surface-container/30 border border-panel-border rounded-xl px-6 py-4 text-white font-black text-lg focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all outline-none"
                        )
                    ]),
                    # PROTOCOLO
                    html.Div(className="col-span-4 space-y-3", children=[
                        html.Label("NET PROTOCOL", className="text-[10px] font-black text-label/40 uppercase tracking-widest px-1"),
                        dcc.Dropdown(
                            id="cli-proto", 
                            options=[{"label": "TCP ENGINE", "value": "tcp"}, {"label": "UDP ENGINE", "value": "udp"}], 
                            value="tcp", 
                            className="nexus-dropdown-premium",
                            clearable=False
                        )
                    ])
                ]),

                # BOTÓN DE ACCIÓN (1:1 Estilo Ejecución)
                html.Button([
                    html.Div(className="flex items-center justify-center gap-4 relative z-10", children=[
                        html.I(className="fas fa-satellite-dish text-xl"),
                        html.Span("EJECUTAR DIAGNÓSTICO ESTRATÉGICO", className="text-[12px] font-black tracking-[0.3em]")
                    ]),
                    html.Div(className="absolute inset-0 bg-white/20 translate-x-[-100%] hover:translate-x-[100%] transition-transform duration-1000 skew-x-12")
                ], id="btn-cli-start", className="w-full h-16 bg-primary text-white rounded-xl relative overflow-hidden transition-all active:scale-95 shadow-xl shadow-primary/20")
            ])
        ]),

        # 2. CABECERA: ANÁLISIS EN TIEMPO REAL (1:1)
        html.Header(className="nx-section-header", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("REAL-TIME DIAGNOSTIC", className="nx-section-header__label"),
            ]),
            html.Span("ESPERANDO ACTIVACIÓN DEL MOTOR", className="nx-section-header__sub")
        ]),

        # ÁREA DE RESULTADOS (Empty State 1:1)
        html.Div(className="dashboard-analytics-wrap flex-1", children=[
            html.Div(className="flex flex-col items-center justify-center h-full p-12 text-center opacity-40 bg-panel-fill/50 border border-dashed border-panel-border rounded-xl", children=[
                html.Div(className="w-20 h-20 rounded-2xl bg-panel-border/30 flex items-center justify-center text-label/20 mb-6 ring-1 ring-white/5 shadow-inner", children=[
                    html.I(className="fas fa-microchip text-3xl")
                ]),
                html.H4("PROCESADOR DE TELEMETRÍA IDLE", className="text-[11px] font-black text-label uppercase tracking-widest italic"),
                html.P("El flujo de datos se visualizará una vez iniciada la conexión con el host", className="text-[9px] text-label/30 font-bold uppercase tracking-[0.2em] mt-3 max-w-xs leading-relaxed")
            ])
        ])
    ])
