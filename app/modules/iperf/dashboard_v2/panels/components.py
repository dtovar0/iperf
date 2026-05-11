"""
components.py — Componentes reutilizables del dashboard iperf.
Single Source of Truth para chart cards, log panels, etc.

Tokens de referencia (tokens.css):
  --text-2xs:  10px   (badges, labels — font-weight ≥ 700)
  --text-xs:   12px   (labels de tabla, meta info)
  --text-sm:   13px   (body small, nav items)
  --color-primary: 37 99 235  (#2563eb)
  --color-accent-sky: 6 182 212  (#06b6d4)
  --color-accent-peach: 245 158 11  (#f59e0b)
"""
from dash import html, dcc


def chart_card(title, icon_cls, accent_color, stat_id, stat_unit, graph_id):
    """
    Tarjeta de gráfica estandarizada para server y client.

    Usa border-panel-border para visibilidad en AMBOS temas (light/dark).
    bg-panel-fill garantiza contraste contra el fondo del body.
    """
    return html.Div(
        className="bg-panel-fill border border-panel-border rounded-panel overflow-hidden flex flex-col flex-1 min-h-0 shadow-sm",
        children=[
            # Header
            html.Div(
                className="p-6 border-b border-panel-border/50 flex-shrink-0 flex justify-between items-center",
                children=[
                    html.Div(className="flex items-center gap-3", children=[
                        html.I(className=f"{icon_cls} text-sm", style={"color": accent_color}),
                        html.Span(title, className="text-2xs font-black uppercase tracking-[0.2em] text-label/60"),
                    ]),
                    html.Div(className="flex items-baseline gap-1", children=[
                        html.Span(id=stat_id, className="text-xl font-black italic text-primary", children="0.00"),
                        html.Span(stat_unit, className="text-2xs font-black text-label/20"),
                    ]),
                ],
            ),
            # Body (Plotly Graph)
            html.Div(className="p-4 flex-1 min-h-0", children=[
                dcc.Graph(
                    id=graph_id,
                    style={"height": "100%", "width": "100%"},
                    config={"displayModeBar": False, "responsive": True},
                ),
            ]),
        ],
    )
