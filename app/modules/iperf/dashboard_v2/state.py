from collections import deque
import threading

MAX_POINTS = 60

# Deques globales (Single Source of Truth)
# Sincronizado con test/app.py
timestamps = deque(maxlen=MAX_POINTS)
recv_mbps  = deque(maxlen=MAX_POINTS)
jitter_ms  = deque(maxlen=MAX_POINTS)
retransmits = deque(maxlen=MAX_POINTS)
log_lines  = deque(maxlen=100)

lock = threading.Lock()

def clear_buffers():
    with lock:
        timestamps.clear()
        recv_mbps.clear()
        jitter_ms.clear()
        retransmits.clear()
        log_lines.clear()
