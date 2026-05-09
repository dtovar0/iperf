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
ACCENT   = "#2563eb" # Nexus Primary Blue
SUCCESS  = "#10b981"
WARNING  = "#f59e0b"
DANGER   = "#ef4444"
DARK     = "#1e293b"
MUTED    = "#64748b"

RL_ACCENT = colors.HexColor(ACCENT)
RL_SUCCESS = colors.HexColor(SUCCESS)
RL_DARK   = colors.HexColor(DARK)
RL_BG     = colors.HexColor(BG)
RL_MUTED  = colors.HexColor(MUTED)
RL_WHITE  = colors.white
RL_WARNING = colors.HexColor(WARNING)
RL_DANGER = colors.HexColor(DANGER)


def _make_chart(ts, values, ylabel, color, title, fill_color=None):
    """Genera una gráfica matplotlib y retorna bytes PNG."""
    fig, ax = plt.subplots(figsize=(7.5, 2.4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(DARK)

    if values:
        ax.plot(range(len(values)), values, color=color, linewidth=2.0, marker='o', markersize=3, markevery=max(1, len(values)//20))
        if fill_color:
            ax.fill_between(range(len(values)), values, alpha=0.1, color=color)
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
    ax.set_title(title, color=RL_ACCENT, fontsize=10, pad=10, fontweight='bold')
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.grid(axis="y", color="#334155", linewidth=0.5, linestyle='--')

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=140, facecolor=BG)
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
    """
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos personalizados ─────────────────────────────────────────────
    title_style = ParagraphStyle(
        "title_style",
        parent=styles["Normal"],
        fontSize=24,
        textColor=RL_ACCENT,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "sub_style",
        parent=styles["Normal"],
        fontSize=10,
        textColor=RL_MUTED,
        spaceAfter=15,
        fontName="Helvetica-Bold",
        textTransform="uppercase",
        letterSpacing=1,
    )
    section_style = ParagraphStyle(
        "section_style",
        parent=styles["Normal"],
        fontSize=12,
        textColor=RL_ACCENT,
        spaceBefore=15,
        spaceAfter=8,
        fontName="Helvetica-Bold",
        textTransform="uppercase",
    )

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph("NEXUS NETWORK TEST", title_style))
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"REPORT ID: {session_data.get('id', 'N/A')} | GENERATED: {generated}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=RL_ACCENT, spaceAfter=20))

    # ── Información de sesión ─────────────────────────────────────────────
    story.append(Paragraph("Session Details", section_style))

    mode       = str(session_data.get("mode", "—")).upper()
    host       = session_data.get("host") or "Localhost"
    port       = session_data.get("port", 5201)
    protocol   = str(session_data.get("protocol") or "tcp").upper()
    parallel   = session_data.get("parallel", 1)
    started_at = session_data.get("started_at", "—")
    ended_at   = session_data.get("ended_at", "—")

    info_data = [
        ["MODE",       mode,       "PORT",    str(port)],
        ["TARGET HOST", host,       "PROTOCOL", protocol],
        ["STREAMS",    str(parallel), "DURATION", f"{session_data.get('duration_s', '—')}s"],
        ["STARTED AT", str(started_at)[:19], "ENDED AT", str(ended_at)[:19]],
    ]

    info_table = Table(info_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR",   (0, 0), (0, -1), RL_MUTED),
        ("TEXTCOLOR",   (2, 0), (2, -1), RL_MUTED),
        ("TEXTCOLOR",   (1, 0), (1, -1), RL_WHITE),
        ("TEXTCOLOR",   (3, 0), (3, -1), RL_WHITE),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0,0), (-1, -1), 8),
    ]))
    story.append(info_table)

    # ── Resumen estadístico ────────────────────────────────────────────────
    story.append(Paragraph("Performance Metrics", section_style))

    summary_data = [
        ["METRIC",               "VALUE",          "UNIT"],
        ["Avg Throughput",       f"{session_data.get('avg_gbps', 0):.3f}", "Gbits/sec"],
        ["Peak Throughput",      f"{session_data.get('max_gbps', 0):.3f}", "Gbits/sec"],
        ["Min Throughput",       f"{session_data.get('min_gbps', 0):.3f}", "Gbits/sec"],
        ["Avg Jitter",           f"{session_data.get('avg_jitter_ms', 0):.3f}", "ms"],
        ["Total Retransmits",    str(session_data.get("total_retransmits", 0)),  "packets"],
        ["Total Samples",        str(session_data.get("total_samples", 0)),     "seconds"],
    ]

    sum_table = Table(summary_data, colWidths=[3.0*inch, 2.0*inch, 2.0*inch])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), RL_ACCENT),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 10),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("BACKGROUND",   (0, 1), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR",    (1, 1), (1, -1), RL_SUCCESS),
        ("FONTNAME",     (1, 1), (1, -1), "Helvetica-Bold"),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    story.append(sum_table)

    # ── Gráficas ──────────────────────────────────────────────────────────
    story.append(Paragraph("Visual Analysis", section_style))

    # Throughput
    gbps_chart = _make_chart(
        ts, gbps_vals,
        ylabel="Gbits/sec", color=ACCENT,
        title="Throughput Stability", fill_color=ACCENT,
    )
    story.append(Image(gbps_chart, width=7.0*inch, height=2.2*inch))
    story.append(Spacer(1, 10))

    # Jitter (solo si hay datos UDP)
    jit_nonzero = [v for v in jitter_vals if v > 0]
    if jit_nonzero:
        jit_ts = [ts[i] for i, v in enumerate(jitter_vals) if v > 0]
        jit_chart = _make_chart(
            jit_ts, jit_nonzero,
            ylabel="ms", color=WARNING,
            title="Jitter Variance (UDP)", fill_color=WARNING,
        )
        story.append(Image(jit_chart, width=7.0*inch, height=2.2*inch))
        story.append(Spacer(1, 10))

    # Retransmisiones (solo si hay datos TCP)
    if any(v > 0 for v in retx_vals):
        retx_chart = _make_chart(
            ts, retx_vals,
            ylabel="retx", color=DANGER,
            title="TCP Retransmissions",
        )
        story.append(Image(retx_chart, width=7.0*inch, height=2.2*inch))

    story.append(Spacer(1, 20))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=RL_MUTED))
    story.append(Paragraph(
        f"Nexus Master Node | Network Orchestrator v2.0 | {generated}",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=8, textColor=RL_MUTED, alignment=1, spaceBefore=5)
    ))

    def dark_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(RL_BG)
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=dark_background, onLaterPages=dark_background)
    buf.seek(0)
    return buf.read()
