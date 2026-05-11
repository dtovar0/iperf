from dash import html, dcc

def get_server_panel():
    return html.Div(id="panel-server", className="flex-1 flex flex-col min-h-0 animate-in fade-in duration-500", children=[
        
        # 1. CABECERA: SÍNTESIS ESTRATÉGICA (1:1 con Portal)
        html.Header(className="nx-section-header", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("SÍNTESIS ESTRATÉGICA", className="nx-section-header__label"),
            ]),
            html.Span("CONTROL OPERATIVO DEL MOTOR", className="nx-section-header__sub")
        ]),
        
        # KPI STRIP (Grid de 5 columnas para paridad 1:1)
        html.Div(className="nx-kpi-strip", children=[
            # MOTOR PRINCIPAL (Card 1)
            html.Div(className="nx-kpi group", style={"--kpi-color": "rgb(var(--color-primary))", "--kpi-color-alpha": "rgb(var(--color-primary) / 0.1)"}, children=[
                html.Div(className="nx-kpi__accent"),
                html.Button([
                    html.Div(className="nx-kpi__header", children=[
                        html.Span("CONTROL CENTRAL", className="nx-kpi__label"),
                        html.Div(className="nx-kpi__icon", children=[html.I(className="fas fa-bolt text-[11px]")])
                    ]),
                    html.Div("INICIAR MOTOR", className="nx-kpi__value text-left !text-[22px]"),
                    html.Div(className="nx-kpi__footer", children=[
                        html.Span("SISTEMA LISTO", className="nx-kpi__trend"),
                        html.Span("ACTIVE", className="nx-kpi__tag")
                    ])
                ], id="btn-srv-start", className="w-full h-full text-left bg-transparent border-none p-0 relative"),
            ]),
            
            # ESTADO (Card 2)
            html.Div(className="nx-kpi", id="srv-status-card", style={"--kpi-color": "#f43f5e", "--kpi-color-alpha": "rgba(244, 63, 94, 0.1)"}, children=[
                html.Div(className="nx-kpi__accent"),
                html.Div(className="nx-kpi__header", children=[
                    html.Span("TELEMETRÍA", className="nx-kpi__label"),
                    html.Div(className="nx-kpi__icon", id="srv-status-icon-container", children=[html.I(id="srv-status-icon", className="fas fa-power-off text-[11px]")])
                ]),
                html.Div(id="srv-status-label", children="OFFLINE", className="nx-kpi__value !text-[22px]"),
                html.Div(className="nx-kpi__footer", children=[
                    html.Span(id="srv-status-desc", children="STANDBY", className="nx-kpi__trend"),
                    html.Span("STATUS", className="nx-kpi__tag")
                ])
            ]),

            # PUERTO (Card 3)
            html.Div(className="nx-kpi", style={"--kpi-color": "#f59e0b", "--kpi-color-alpha": "rgba(245, 158, 11, 0.1)"}, children=[
                html.Div(className="nx-kpi__accent"),
                html.Div(className="nx-kpi__header", children=[
                    html.Span("GATEWAY", className="nx-kpi__label"),
                    html.Div(className="nx-kpi__icon", children=[html.I(className="fas fa-plug text-[11px]")])
                ]),
                dcc.Input(id="srv-port", type="number", value=5201, className="nx-kpi__value !text-[22px] bg-transparent border-none p-0 focus:ring-0 w-full [appearance:textfield]"),
                html.Div(className="nx-kpi__footer", children=[
                    html.Span("PUERTO TCP", className="nx-kpi__trend"),
                    html.Span("PORT", className="nx-kpi__tag")
                ])
            ]),

            # EMERGENCIA (Card 4)
            html.Div(className="nx-kpi group", style={"--kpi-color": "#ef4444", "--kpi-color-alpha": "rgba(239, 68, 68, 0.1)"}, children=[
                html.Div(className="nx-kpi__accent"),
                html.Button([
                    html.Div(className="nx-kpi__header", children=[
                        html.Span("SEGURIDAD", className="nx-kpi__label"),
                        html.Div(className="nx-kpi__icon", children=[html.I(className="fas fa-stop text-[11px]")])
                    ]),
                    html.Div("DETENER", className="nx-kpi__value text-left !text-[22px]"),
                    html.Div(className="nx-kpi__footer", children=[
                        html.Span("FORCE STOP", className="nx-kpi__trend"),
                        html.Span("KILL", className="nx-kpi__tag")
                    ])
                ], id="btn-srv-stop", className="w-full h-full text-left bg-transparent border-none p-0 relative"),
            ]),
            
            # RESERVADO (Card 5 - para mantener el grid de 5)
            html.Div(className="nx-kpi opacity-20", children=[
                html.Div(className="nx-kpi__accent"),
                html.Div(className="nx-kpi__header", children=[
                    html.Span("RESERVADO", className="nx-kpi__label"),
                    html.Div(className="nx-kpi__icon", children=[html.I(className="fas fa-microchip text-[11px]")])
                ]),
                html.Div("0", className="nx-kpi__value !text-[22px]"),
                html.Div(className="nx-kpi__footer", children=[
                    html.Span("SIN CAMBIO", className="nx-kpi__trend"),
                    html.Span("IDLE", className="nx-kpi__tag")
                ])
            ])
        ]),

        # 2. CABECERA: ANÁLISIS OPERATIVO (1:1 con Portal)
        html.Header(className="nx-section-header", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("ANÁLISIS OPERATIVO", className="nx-section-header__label"),
            ]),
            html.Span("MÉTRICAS DE RENDIMIENTO Y FLUJO", className="nx-section-header__sub")
        ]),

        # GRID ANALYTICS 1:1
        html.Div(className="dashboard-analytics-wrap", children=[
            html.Div(className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 min-h-0", children=[
                
                # ÁREA DE GRÁFICAS (2/3 del espacio)
                html.Div(className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-8 min-h-0", children=[
                    # Throughput
                    html.Div(className="bg-panel-fill border border-panel-border rounded-xl p-6 flex flex-col shadow-sm gap-4 overflow-hidden h-full", children=[
                        html.Header(className="flex items-center justify-between", children=[
                            html.Div(className="flex items-center gap-2", children=[
                                html.Div(className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center text-primary text-[10px]", children=[html.I(className="fas fa-chart-line")]),
                                html.H3("THROUGHPUT STABILITY", className="text-[9px] font-black text-label uppercase tracking-widest"),
                            ]),
                            html.Div([
                                html.Span(id="current-bw", className="text-xl font-black text-primary italic", children="0.00"),
                                html.Span(" GBPS", className="text-[8px] font-black text-label/20 ml-1")
                            ])
                        ]),
                        html.Div(className="flex-1 chart-container-box", children=[
                            dcc.Graph(id="bw-chart", className="h-full w-full", config={'displayModeBar': False})
                        ])
                    ]),
                    
                    # Latency
                    html.Div(className="bg-panel-fill border border-panel-border rounded-xl p-6 flex flex-col shadow-sm gap-4 overflow-hidden h-full", children=[
                        html.Header(className="flex items-center justify-between", children=[
                            html.Div(className="flex items-center gap-2", children=[
                                html.Div(className="w-6 h-6 rounded bg-amber-500/10 flex items-center justify-center text-amber-500 text-[10px]", children=[html.I(className="fas fa-wave-square")]),
                                html.H3("LATENCY VARIANCE", className="text-[9px] font-black text-label uppercase tracking-widest"),
                            ]),
                            html.Div([
                                html.Span(id="stat-jitter", className="text-xl font-black text-amber-500 italic", children="0.000"),
                                html.Span(" MS", className="text-[8px] font-black text-label/20 ml-1")
                            ])
                        ]),
                        html.Div(className="flex-1 chart-container-box", children=[
                            dcc.Graph(id="jitter-chart", className="h-full w-full", config={'displayModeBar': False})
                        ])
                    ]),
                ]),

                # ÁREA DE LOGS (1/3 del espacio - como la Telemetría Global del portal)
                html.Div(className="bg-panel-fill border border-panel-border rounded-xl flex flex-col shadow-2xl overflow-hidden min-h-0", children=[
                    html.Header(className="shrink-0 p-6 border-b border-panel-border bg-surface-container/20 flex items-center justify-between", children=[
                        html.Span("TELEMETRÍA GLOBAL", className="text-xs font-black text-label uppercase tracking-widest"),
                        html.Button([
                            html.I(className="fas fa-trash-alt text-xs"),
                        ], id="btn-clear", className="w-8 h-8 rounded-lg bg-surface-container hover:bg-primary/20 text-label/30 hover:text-primary transition-all flex items-center justify-center")
                    ]),
                    
                    # Body Terminal
                    html.Div(id="log-container", className="flex-1 p-6 font-mono text-[11px] overflow-y-auto custom-scrollbar bg-black/20", children=[
                        html.Pre(id="log-output", className="text-emerald-500/60 leading-relaxed whitespace-pre-wrap", children="[NEXUS] Esperando transmisión..."),
                    ]),
                    
                    # Footer
                    html.Footer(className="p-4 border-t border-panel-border bg-surface-container/10 flex justify-between items-center", children=[
                        html.P("iperf3 engine", className="text-[9px] font-mono text-label/20 tracking-widest uppercase"),
                        html.P(id="last-update", children="IDLE", className="text-[9px] font-mono text-primary/20 font-black tracking-widest")
                    ])
                ])
            ])
        ])
    ])
