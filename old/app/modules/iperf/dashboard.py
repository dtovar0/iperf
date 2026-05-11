"""
Refactor del Dashboard de iperf3 (v2 Modular)
Este archivo ahora actúa como un proxy para la nueva estructura organizada en el directorio dashboard_v2/
"""

from app.modules.iperf.dashboard_v2 import init_dashboard, lock, timestamps, recv_mbps, jitter_ms, retransmits, log_lines

# Re-exportamos init_dashboard para mantener compatibilidad con app/__init__.py
__all__ = ['init_dashboard', 'lock', 'timestamps', 'recv_mbps', 'jitter_ms', 'retransmits', 'log_lines']
