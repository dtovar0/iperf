from dash import html, dcc

def get_history_panel():
    return html.Div(id="panel-history", className="hidden animate-in fade-in duration-500 flex flex-col min-h-0", children=[
        
        # 1. CABECERA: HISTORY ARCHIVE
        html.Header(className="nx-section-header", children=[
            html.Div(className="nx-section-header__left", children=[
                html.Div(className="nx-section-header__rule"),
                html.H3("HISTORY ARCHIVE", className="nx-section-header__label"),
            ]),
            html.Button([
                html.I(className="fas fa-sync-alt mr-3 group-hover:rotate-180 transition-transform duration-700"),
                html.Span("REFRESCAR")
            ], id="btn-history-refresh", className="bg-primary/10 hover:bg-primary text-primary hover:text-white px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all flex items-center group shadow-lg shadow-primary/5")
        ]),

        # CUERPO PRINCIPAL
        html.Div(className="dashboard-analytics-wrap flex-1 flex flex-col min-h-0", children=[
            
            # FILTROS Y BÚSQUEDA
            html.Div(className="flex flex-shrink-0 justify-between items-center gap-6 mb-8", children=[
                html.Div(className="relative group flex-grow max-w-xl", children=[
                    html.I(className="fas fa-search absolute left-6 top-1/2 -translate-y-1/2 text-label/20 group-focus-within:text-primary transition-colors z-10"),
                    dcc.Input(
                        type="text",
                        id="history-search",
                        placeholder="Filtrar registros por host, fecha o ID...",
                        className="w-full bg-panel-fill border border-panel-border rounded-xl pl-14 pr-6 py-4 text-sm font-bold text-body-text outline-none focus:border-primary/40 focus:ring-4 focus:ring-primary/5 transition-all placeholder:text-label/10 shadow-sm"
                    )
                ]),
                html.Div(className="px-6 py-3 rounded-xl bg-panel-fill border border-panel-border flex items-center gap-4", children=[
                    html.Span("REGISTROS:", className="text-[9px] font-black text-label/20 tracking-[0.2em]"),
                    html.Span("ÚLTIMOS 50", className="text-[9px] font-black text-primary tracking-[0.2em]"),
                ])
            ]),

            # CONTENEDOR DE TABLA (Premium Grid)
            html.Div(className="flex-1 min-h-0 bg-panel-fill border border-panel-border rounded-xl flex flex-col shadow-2xl overflow-hidden", children=[
                html.Div(className="overflow-y-auto custom-scrollbar flex-1", children=[
                    html.Table(className="w-full text-left border-collapse", children=[
                        html.Thead(className="sticky top-0 z-20 bg-surface-container/95 backdrop-blur-md", children=[
                            html.Tr(className="text-[10px] font-black text-label/30 uppercase tracking-[0.3em] border-b border-panel-border", children=[
                                html.Th("ID", className="py-6 px-8"),
                                html.Th("MODO", className="py-6 px-4 text-center"),
                                html.Th("PROT", className="py-6 px-4 text-center"),
                                html.Th("GATEWAY / DESTINO", className="py-6 px-4"),
                                html.Th("RESULTADO", className="py-6 px-4 text-center"),
                                html.Th("TIMESTAMP", className="py-6 px-4 text-center"),
                                html.Th("REPORTE", className="py-6 px-8 text-right"),
                            ])
                        ]),
                        html.Tbody(id="history-list", className="divide-y divide-panel-border/30")
                    ])
                ])
            ])
        ])
    ])
