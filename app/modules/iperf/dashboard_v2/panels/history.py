from dash import html, dcc

def get_history_panel():
    return html.Div(id="panel-history", className="iperf-panel hidden h-full", children=[
        
        # FILA 0: HEADER CONFIGURACIÓN
        html.Header(className="flex-shrink-0 nx-section-header !pb-2", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("ARCHIVO DE RESULTADOS", className="nx-section-header__label"),
            ]),
            html.Button([
                html.I(className="fas fa-sync-alt mr-3 group-hover:rotate-180 transition-transform duration-700"),
                html.Span("REFRESCAR")
            ], id="btn-history-refresh", className="bg-primary/10 hover:bg-primary text-primary hover:text-white px-6 py-3 rounded-base text-2xs font-black uppercase tracking-[0.2em] transition-all flex items-center group")
        ]),

        # FILA 1: FILTROS Y BÚSQUEDA (Control Bar Style)
        html.Div(className="flex-shrink-0 flex items-center gap-4 p-4 bg-panel-fill border border-panel-border rounded-panel shadow-sm mb-4", children=[
            # Búsqueda
            html.Div(className="flex-1 flex items-center gap-3", children=[
                html.I(className="fas fa-search text-label/20 text-sm"),
                dcc.Input(
                    type="text",
                    id="history-search",
                    placeholder="FILTRAR POR HOST, FECHA O ID...",
                    className="iperf-input flex-1"
                )
            ]),

            html.Div(className="w-px h-8 bg-panel-border/30 mx-2"),

            # Stats
            html.Div(className="flex items-center gap-3 px-4 py-2 rounded-base border border-panel-border/30 bg-surface-container/30", children=[
                html.Span("REGISTROS:", className="text-2xs font-black text-label/20 tracking-widest"),
                html.Span("ÚLTIMOS 50", className="text-2xs font-black text-primary tracking-widest"),
            ])
        ]),

        # FILA 2: TABLA DE RESULTADOS
        html.Div(className="flex-1 min-h-0 bg-panel-fill border border-panel-border rounded-panel flex flex-col shadow-2xl overflow-hidden", children=[
            html.Div(className="overflow-y-auto custom-scrollbar flex-1", children=[
                html.Table(className="w-full text-left border-collapse", children=[
                    html.Thead(className="sticky top-0 z-20 bg-surface-container/95 backdrop-blur-md", children=[
                        html.Tr(className="text-2xs font-black text-label/30 uppercase tracking-[0.3em] border-b border-panel-border", children=[
                            html.Th("ID", className="py-5 px-8"),
                            html.Th("MODO", className="py-5 px-4 text-center"),
                            html.Th("PROT", className="py-5 px-4 text-center"),
                            html.Th("GATEWAY / DESTINO", className="py-5 px-4"),
                            html.Th("RESULTADO", className="py-5 px-4 text-center"),
                            html.Th("FECHA / HORA", className="py-5 px-4 text-center"),
                            html.Th("REPORTE", className="py-5 px-8 text-right"),
                        ])
                    ]),
                    html.Tbody(id="history-list", className="divide-y divide-panel-border/10")
                ])
            ])
        ])
    ])
