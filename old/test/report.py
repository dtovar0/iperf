"""
report.py — Generación de PDF de reporte para iperf3 Dashboard.
Usa reportlab para el layout y matplotlib para las gráficas.
"""

import io
import os
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # sin display
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable,
)

# ── Paleta ────────────────────────────────────────────────────────────────────
BG       = "#0f1117"
ACCENT   = "#00d4ff"
GREEN    = "#00ff9d"
YELLOW   = "#ffd166"
RED_C    = "#ff6b6b"
DARK     = "#1a1d2e"
MUTED    = "#64748b"

RL_ACCENT = colors.HexColor(ACCENT)
RL_GREEN  = colors.HexColor(GREEN)
RL_DARK   = colors.HexColor(DARK)
RL_BG     = colors.HexColor(BG)
RL_MUTED  = colors.HexColor(MUTED)
RL_WHITE  = colors.white
RL_YELLOW = colors.HexColor(YELLOW)
RL_RED    = colors.HexColor(RED_C)


def _make_chart(ts, values, ylabel, color, title, fill_color=None):
    """Genera una gráfica matplotlib y retorna bytes PNG."""
    fig, ax = plt.subplots(figsize=(7.5, 2.4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(DARK)

    if values:
        ax.plot(range(len(values)), values, color=color, linewidth=1.8)
        if fill_color:
            ax.fill_between(range(len(values)), values, alpha=0.15, color=color)
        ax.set_xlim(0, max(len(values) - 1, 1))
        ax.set_ylim(bottom=0)

    # Ticks de X con timestamps
    if ts and len(ts) > 1:
        step = max(1, len(ts) // 8)
        ax.set_xticks(range(0, len(ts), step))
        ax.set_xticklabels([ts[i] for i in range(0, len(ts), step)],
                           fontsize=7, color=MUTED, rotation=20)
    else:
        ax.set_xticks([])

    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))
    ax.tick_params(axis="y", colors=MUTED, labelsize=7)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=8)
    ax.set_title(title, color=ACCENT, fontsize=9, pad=6)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3748")
    ax.grid(axis="y", color="#2d3748", linewidth=0.5)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_report(
    session_data: dict,
    ts:          list,
    gbps_vals:   list,
    jitter_vals: list,
    retx_vals:   list,
) -> bytes:
    """
    Genera el PDF y retorna los bytes.

    session_data: {
        mode, host, port, protocol, parallel,
        started_at, ended_at,
        avg_gbps, max_gbps, min_gbps,
        avg_jitter_ms, total_retransmits, total_samples
    }
    """
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos personalizados ─────────────────────────────────────────────
    title_style = ParagraphStyle(
        "title_style",
        parent=styles["Normal"],
        fontSize=20,
        textColor=RL_ACCENT,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "sub_style",
        parent=styles["Normal"],
        fontSize=9,
        textColor=RL_MUTED,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "section_style",
        parent=styles["Normal"],
        fontSize=11,
        textColor=RL_ACCENT,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    normal_style = ParagraphStyle(
        "normal_style",
        parent=styles["Normal"],
        fontSize=9,
        textColor=RL_WHITE,
    )

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph("⚡ iperf3 — Reporte de prueba", title_style))
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generado: {generated}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=RL_ACCENT))
    story.append(Spacer(1, 10))

    # ── Información de sesión ─────────────────────────────────────────────
    story.append(Paragraph("Información de sesión", section_style))

    mode       = session_data.get("mode", "—").upper()
    host       = session_data.get("host") or "—"
    port       = session_data.get("port", "—")
    protocol   = (session_data.get("protocol") or "tcp").upper()
    parallel   = session_data.get("parallel", 1)
    started_at = session_data.get("started_at", "—")
    ended_at   = session_data.get("ended_at", "—")

    # Calcular duración
    try:
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        if isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at)
        duration = str(ended_at - started_at).split(".")[0]
    except Exception:
        duration = "—"

    info_data = [
        ["Modo",       mode,       "Puerto",    str(port)],
        ["Host",       host,       "Protocolo", protocol],
        ["Streams -P", str(parallel), "Duración", duration],
        ["Inicio",     str(started_at)[:19], "Fin", str(ended_at)[:19]],
    ]

    info_table = Table(info_data, colWidths=[1.1*inch, 2.3*inch, 1.1*inch, 2.3*inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), RL_DARK),
        ("TEXTCOLOR",   (0, 0), (0, -1), RL_MUTED),
        ("TEXTCOLOR",   (2, 0), (2, -1), RL_MUTED),
        ("TEXTCOLOR",   (1, 0), (1, -1), RL_WHITE),
        ("TEXTCOLOR",   (3, 0), (3, -1), RL_WHITE),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [RL_DARK, colors.HexColor("#1f2438")]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#2d3748")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # ── Resumen estadístico ────────────────────────────────────────────────
    story.append(Paragraph("Resumen estadístico", section_style))

    avg_gbps  = session_data.get("avg_gbps")
    max_gbps  = session_data.get("max_gbps")
    min_gbps  = session_data.get("min_gbps")
    avg_jit   = session_data.get("avg_jitter_ms")
    total_retx= session_data.get("total_retransmits", 0)
    samples   = session_data.get("total_samples", len(ts))

    def fmt(v, decimals=2):
        return f"{v:.{decimals}f}" if v is not None else "—"

    summary_data = [
        ["Métrica",               "Valor",          "Unidad"],
        ["Throughput promedio",   fmt(avg_gbps, 3), "Gbits/sec"],
        ["Throughput máximo",     fmt(max_gbps, 3), "Gbits/sec"],
        ["Throughput mínimo",     fmt(min_gbps, 3), "Gbits/sec"],
        ["Jitter promedio",       fmt(avg_jit,  3), "ms"],
        ["Retransmisiones total", str(total_retx),  "paquetes"],
        ["Muestras",              str(samples),     "segundos"],
    ]

    col_w = [2.8*inch, 2.0*inch, 2.0*inch]
    sum_table = Table(summary_data, colWidths=col_w)
    sum_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#0d1117")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), RL_ACCENT),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        # Body
        ("BACKGROUND",   (0, 1), (-1, -1), RL_DARK),
        ("ROWBACKGROUNDS",(0,1), (-1, -1), [RL_DARK, colors.HexColor("#1f2438")]),
        ("TEXTCOLOR",    (0, 1), (0, -1), RL_MUTED),
        ("TEXTCOLOR",    (1, 1), (1, -1), RL_GREEN),
        ("TEXTCOLOR",    (2, 1), (2, -1), RL_MUTED),
        ("FONTNAME",     (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("ALIGN",        (1, 0), (2, -1), "CENTER"),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#2d3748")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 14))

    # ── Gráficas ──────────────────────────────────────────────────────────
    story.append(Paragraph("Gráficas de rendimiento", section_style))

    # Throughput
    gbps_chart = _make_chart(
        ts, gbps_vals,
        ylabel="Gbits/sec", color=ACCENT,
        title="Throughput (Gbits/sec)", fill_color=ACCENT,
    )
    story.append(Image(gbps_chart, width=6.8*inch, height=2.1*inch))
    story.append(Spacer(1, 8))

    # Jitter (solo si hay datos UDP)
    jit_nonzero = [v for v in jitter_vals if v > 0]
    if jit_nonzero:
        jit_ts = [ts[i] for i, v in enumerate(jitter_vals) if v > 0]
        jit_chart = _make_chart(
            jit_ts, jit_nonzero,
            ylabel="ms", color=YELLOW,
            title="Jitter (ms) · UDP", fill_color=YELLOW,
        )
        story.append(Image(jit_chart, width=6.8*inch, height=2.0*inch))
        story.append(Spacer(1, 8))

    # Retransmisiones (solo si hay datos TCP)
    if any(v > 0 for v in retx_vals):
        retx_chart = _make_chart(
            ts, retx_vals,
            ylabel="retx", color=RED_C,
            title="Retransmisiones · TCP",
        )
        story.append(Image(retx_chart, width=6.8*inch, height=2.0*inch))

    story.append(Spacer(1, 14))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=RL_MUTED))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"iperf3 Dashboard · {generated}",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=7, textColor=RL_MUTED, alignment=1)
    ))

    # ── Fondo oscuro en todas las páginas ─────────────────────────────────
    def dark_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(RL_BG)
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=dark_background, onLaterPages=dark_background)
    buf.seek(0)
    return buf.read()
