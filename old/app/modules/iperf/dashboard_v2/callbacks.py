from dash import Output, Input, State, callback_context, no_update, html
from flask_login import current_user
from datetime import datetime
import plotly.graph_objs as go

from app.modules.iperf.services import IperfService

def register_callbacks(dash_app, lock, timestamps, recv_mbps, jitter_ms, retransmits, log_lines, empty_graph):
    
    # ─── NAVEGACIÓN SPA ───
    @dash_app.callback(
        [Output("panel-server", "className"),
         Output("panel-client", "className"),
         Output("panel-history", "className")],
        [Input("url", "pathname")],
        prevent_initial_call=False
    )
    def switch_tabs(pathname):
        panel_active = "flex-1 min-h-0 flex flex-col animate-in fade-in duration-500 overflow-hidden"
        panel_hidden = "hidden"

        # Normalizar el pathname para manejar el prefijo /iperf/
        path = pathname.rstrip('/') if pathname else ""
        
        if path == "/iperf/server" or path == "/iperf":
            return panel_active, panel_hidden, panel_hidden
        elif path == "/iperf/client":
            return panel_hidden, panel_active, panel_hidden
        elif path == "/iperf/history":
            return panel_hidden, panel_hidden, panel_active
            
        return panel_active, panel_hidden, panel_hidden

    # ─── CONTROL DE SERVICIO (SERVIDOR) ───
    @dash_app.callback(
        [Output("srv-status-icon-container", "className"),
         Output("srv-status-icon", "className"),
         Output("srv-status-label", "children"),
         Output("srv-status-label", "className"),
         Output("srv-status-desc", "children")],
        [Input("btn-srv-start", "n_clicks"),
         Input("btn-srv-stop", "n_clicks")],
        [State("srv-port", "value")],
        prevent_initial_call=True
    )
    def control_server(n_start, n_stop, srv_port):
        ctx = callback_context
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if btn_id == "btn-srv-start":
            success, msg = IperfService.start_server(current_user.id, srv_port)
            if success:
                return "w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)] animate-pulse", \
                       "fas fa-check-circle", \
                       "ACTIVO", "text-xl font-black text-emerald-500 italic leading-none", \
                       f"Escuchando en puerto {srv_port}"
            else:
                return "w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.3)]", \
                       "fas fa-exclamation-triangle", \
                       "OCUPADO", "text-xl font-black text-amber-500 italic leading-none", \
                       msg.upper()
        
        elif btn_id == "btn-srv-stop":
            IperfService.stop_server(current_user.id)
            return "w-10 h-10 rounded-xl bg-rose-500/10 flex items-center justify-center text-rose-500", \
                   "fas fa-power-off", \
                   "ABAJO", "text-xl font-black text-rose-500 italic leading-none", \
                   f"Puerto {srv_port} Disponible"
        
        return no_update

    # ─── ACTUALIZACIÓN DE MÉTRICAS (DESDE MEMORIA) ───
    @dash_app.callback(
        [Output("bw-chart", "figure"),
         Output("jitter-chart", "figure"),
         Output("current-bw", "children"),
         Output("stat-jitter", "children"),
         Output("log-output", "children"),
         Output("last-update", "children"),
         Output("modal-summary", "className"),
         Output("modal-msg", "children"),
         Output("modal-download-link", "href")],
        [Input("interval-update", "n_intervals")],
        [State("ui-state", "data")],
        prevent_initial_call=False
    )
    def update_dashboard(n, ui_state):
        from app.modules.iperf.models import IperfSession
        
        # 1. Buscar la sesión más reciente del usuario
        session = IperfSession.query.filter_by(user_id=current_user.id)\
                                    .order_by(IperfSession.id.desc())\
                                    .first()
        
        if not session:
            return empty_graph(), empty_graph(), "0.00", "0.000", "Esperando sesión...", datetime.now().strftime('%H:%M:%S'), "hidden", "", "#"

        live_session = IperfService._live_data.get(session.id)
        
        # Caso: No hay datos aún
        if not live_session or not live_session["measurements"]:
            return empty_graph(), empty_graph(), "0.00", "0.000", "Inicializando buffer...", datetime.now().strftime('%H:%M:%S'), "hidden", "", "#"

        # 3. Preparar datos para gráficas
        meas = live_session["measurements"]
        x = [m["timestamp"] for m in meas]
        y_bw = [m["gbps"] for m in meas]
        y_jitter = [m["jitter"] for m in meas]
        
        bw_fig = {
            "data": [go.Scatter(x=x, y=y_bw, mode='lines', line=dict(color='#2563eb', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(37,99,235,0.08)')],
            "layout": go.Layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=48, r=12, t=8, b=36),
                xaxis=dict(showgrid=False, color="#64748b", tickangle=0, nticks=5),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="#64748b", zeroline=False)
            )
        }
        
        jitter_fig = {
            "data": [go.Scatter(x=x, y=y_jitter, mode='lines', line=dict(color='#f59e0b', width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(245,158,11,0.05)')],
            "layout": go.Layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=48, r=12, t=8, b=36),
                xaxis=dict(showgrid=False, color="#64748b", tickangle=0, nticks=5),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="#64748b", zeroline=False)
            )
        }
        
        logs = "\n".join(live_session["logs"][-100:])
        cur_bw = f"{y_bw[-1]:.2f}"
        cur_jitter = f"{y_jitter[-1]:.3f}"
        last_sync = datetime.now().strftime('%H:%M:%S')

        # 4. Verificar si el test terminó para mostrar el modal
        modal_class = "hidden"
        modal_msg = ""
        
        # Si hay un resumen generado, significa que el proceso de iperf terminó
        if live_session["summary"]:
            s = live_session["summary"]
            modal_class = "fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md animate-in fade-in duration-300"
            modal_msg = f"Throughput Promedio: {s['avg_gbps']:.2f} Gbps | Jitter: {s['avg_jitter_ms']:.3f} ms"

        report_url = f"/iperf/report/{session.id}" if session else "#"
        return bw_fig, jitter_fig, cur_bw, cur_jitter, logs, last_sync, modal_class, modal_msg, report_url

    # ─── ACCIONES DEL MODAL ───
    @dash_app.callback(
        Output("ui-state", "data", allow_duplicate=True),
        [Input("btn-modal-close", "n_clicks"),
         Input("btn-save-db", "n_clicks")],
        [State("ui-state", "data")],
        prevent_initial_call=True
    )
    def handle_modal_actions(n_close, n_save, ui_state):
        ctx = callback_context
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        from app.modules.iperf.models import IperfSession, IperfMeasurement, IperfSessionSummary
        from app import db
        
        session = IperfSession.query.filter_by(user_id=current_user.id)\
                                    .order_by(IperfSession.id.desc())\
                                    .first()
        
        if not session: return ui_state

        if btn_id == "btn-save-db":
            live = IperfService._live_data.get(session.id)
            if live and live["measurements"]:
                # Guardar mediciones
                for m in live["measurements"]:
                    meas = IperfMeasurement(
                        session_id=session.id,
                        gbps=m["gbps"],
                        jitter_ms=m["jitter"],
                        retransmits=m["retx"]
                    )
                    db.session.add(meas)
                
                # Guardar resumen
                s = live["summary"]
                summary = IperfSessionSummary(
                    session_id=session.id,
                    avg_gbps=s["avg_gbps"],
                    max_gbps=s["max_gbps"],
                    min_gbps=s["min_gbps"],
                    avg_jitter_ms=s["avg_jitter_ms"],
                    total_samples=s["total_samples"]
                )
                db.session.add(summary)
                
                session.status = 'completed'
                db.session.commit()
            
        # Limpiar memoria en cualquier caso (Cerrar o Guardar)
        if session.id in IperfService._live_data:
            # IperfService._live_data.pop(session.id) # Comentado para no romper el refresh mientras el modal cierra
            IperfService._live_data[session.id]["summary"] = None # Reset para ocultar el modal
            
        return ui_state
    # ─── HISTORIAL DE SESIONES ───
    @dash_app.callback(
        Output("history-list", "children"),
        [Input("btn-history-refresh", "n_clicks"),
         Input("url", "pathname")],
        prevent_initial_call=False
    )
    def update_history(n, pathname):
        from app.modules.iperf.models import IperfSession
        
        # Obtener las últimas 50 sesiones del usuario
        sessions = IperfSession.query.filter_by(user_id=current_user.id)\
                                     .order_by(IperfSession.id.desc())\
                                     .limit(50).all()
        
        if not sessions:
            return [html.Tr([
                html.Td("No hay registros disponibles", colSpan=7, className="py-10 text-center text-label/20 font-black italic")
            ])]

        rows = []
        for s in sessions:
            # Badge de Modo
            mode_color = "text-emerald-500 bg-emerald-500/10" if s.mode == 'server' else "text-primary bg-primary/10"
            mode_badge = html.Span(s.mode.upper(), className=f"px-3 py-1 rounded-lg text-[10px] font-black tracking-widest {mode_color}")

            # Badge de Protocolo
            proto_color = "text-amber-500 bg-amber-500/10" if s.protocol == 'udp' else "text-sky-500 bg-sky-500/10"
            proto_badge = html.Span(s.protocol.upper(), className=f"px-3 py-1 rounded-lg text-[10px] font-black tracking-widest {proto_color}")

            # Resultado (Throughput)
            bw_text = "--"
            if s.summary:
                bw_text = f"{s.summary.avg_gbps:.2f} Gbps"
            elif s.status == 'running':
                bw_text = "EN CURSO..."
            
            rows.append(html.Tr(className="hover:bg-white/5 transition-colors group", children=[
                html.Td(f"#{s.id}", className="py-4 px-6 text-xs font-black text-label/40"),
                html.Td(mode_badge, className="py-4 px-4 text-center"),
                html.Td(proto_badge, className="py-4 px-4 text-center"),
                html.Td(s.host or "LOCALHOST", className="py-4 px-4 text-xs font-bold text-text truncate"),
                html.Td(bw_text, className="py-4 px-4 text-center text-xs font-black text-emerald-500"),
                html.Td(s.started_at.strftime("%d/%m/%Y %H:%M") if s.started_at else "--", className="py-4 px-4 text-center text-[10px] font-bold text-label/40"),
                html.Td(className="py-4 px-6 text-right", children=[
                    html.A(html.I(className="fas fa-file-pdf"), 
                           href=f"/iperf/report/{s.id}", 
                           target="_blank",
                           className="text-primary/40 hover:text-primary transition-all p-2")
                ])
            ]))
        
        return rows
