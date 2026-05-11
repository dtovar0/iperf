"""
database.py — Conexión MySQL y operaciones de reportes para iperf3 Dashboard.

Tablas:
  sessions        → una fila por prueba (servidor o cliente)
  measurements    → un punto por segundo de medición
  session_summary → resumen calculado al cerrar la sesión
"""

import mysql.connector
from mysql.connector import pooling
import os
import time
from datetime import datetime

# ── Configuración ─────────────────────────────────────────────────────────────
# Puedes sobreescribir con variables de entorno o editar aquí directamente.
DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST",     "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", "3306")),
    "user":     os.getenv("MYSQL_USER",     "iperf3_user"),
    "password": os.getenv("MYSQL_PASSWORD", "changeme"),
    "database": os.getenv("MYSQL_DATABASE", "iperf3_db"),
    "charset":  "utf8mb4",
}

# Pool de conexiones (evita abrir/cerrar por cada operación)
_pool: pooling.MySQLConnectionPool | None = None


def get_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="iperf3_pool",
            pool_size=5,
            **DB_CONFIG,
        )
    return _pool


def get_conn():
    """Obtiene una conexión del pool."""
    return get_pool().get_connection()


# ── Schema ────────────────────────────────────────────────────────────────────
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id            BIGINT       AUTO_INCREMENT PRIMARY KEY,
    mode          ENUM('server','client')  NOT NULL,
    host          VARCHAR(64)  DEFAULT NULL,   -- solo cliente
    port          SMALLINT     NOT NULL,
    protocol      ENUM('tcp','udp') NOT NULL DEFAULT 'tcp',
    parallel      TINYINT      NOT NULL DEFAULT 1,
    duration_s    SMALLINT     DEFAULT NULL,   -- solo cliente
    started_at    DATETIME     NOT NULL,
    ended_at      DATETIME     DEFAULT NULL,
    status        ENUM('running','completed','aborted') NOT NULL DEFAULT 'running',
    INDEX idx_started (started_at),
    INDEX idx_mode    (mode)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS measurements (
    id            BIGINT       AUTO_INCREMENT PRIMARY KEY,
    session_id    BIGINT       NOT NULL,
    measured_at   DATETIME(3)  NOT NULL,       -- precisión milisegundos
    gbps          FLOAT        NOT NULL,
    jitter_ms     FLOAT        NOT NULL DEFAULT 0,
    retransmits   INT          NOT NULL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_time    (measured_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS session_summary (
    session_id       BIGINT  PRIMARY KEY,
    avg_gbps         FLOAT   NOT NULL,
    max_gbps         FLOAT   NOT NULL,
    min_gbps         FLOAT   NOT NULL,
    avg_jitter_ms    FLOAT   NOT NULL DEFAULT 0,
    total_retransmits INT    NOT NULL DEFAULT 0,
    total_samples    INT     NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB;
"""


def init_schema():
    """Crea las tablas si no existen. Llama esto al arrancar la app."""
    conn = get_conn()
    cur  = conn.cursor()
    for stmt in SCHEMA_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()
    print("[DB] Schema listo.")


# ── Operaciones de sesión ─────────────────────────────────────────────────────

def session_start(mode: str, port: int, protocol: str = "tcp",
                  parallel: int = 1, host: str = None,
                  duration_s: int = None) -> int:
    """
    Registra el inicio de una sesión (servidor o cliente).
    Retorna el session_id generado.
    """
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (mode, host, port, protocol, parallel, duration_s, started_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'running')
    """, (mode, host, port, protocol, parallel, duration_s, datetime.now()))
    session_id = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return session_id


def session_end(session_id: int, status: str = "completed"):
    """
    Marca la sesión como terminada y calcula el resumen automáticamente.
    status: 'completed' | 'aborted'
    """
    conn = get_conn()
    cur  = conn.cursor()

    # Cerrar sesión
    cur.execute("""
        UPDATE sessions SET ended_at = %s, status = %s WHERE id = %s
    """, (datetime.now(), status, session_id))

    # Calcular y guardar resumen desde las mediciones
    cur.execute("""
        INSERT INTO session_summary
            (session_id, avg_gbps, max_gbps, min_gbps,
             avg_jitter_ms, total_retransmits, total_samples)
        SELECT
            %s,
            AVG(gbps),  MAX(gbps),  MIN(gbps),
            AVG(jitter_ms),
            SUM(retransmits),
            COUNT(*)
        FROM measurements
        WHERE session_id = %s
        ON DUPLICATE KEY UPDATE
            avg_gbps          = VALUES(avg_gbps),
            max_gbps          = VALUES(max_gbps),
            min_gbps          = VALUES(min_gbps),
            avg_jitter_ms     = VALUES(avg_jitter_ms),
            total_retransmits = VALUES(total_retransmits),
            total_samples     = VALUES(total_samples)
    """, (session_id, session_id))

    conn.commit()
    cur.close()
    conn.close()


def save_measurement(session_id: int, gbps: float,
                     jitter_ms: float = 0, retransmits: int = 0):
    """Guarda un punto de medición (llamado cada segundo)."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO measurements (session_id, measured_at, gbps, jitter_ms, retransmits)
        VALUES (%s, %s, %s, %s, %s)
    """, (session_id, datetime.now(), gbps, jitter_ms, retransmits))
    conn.commit()
    cur.close()
    conn.close()


def save_measurements_bulk(session_id: int, points: list[dict]):
    """
    Guarda múltiples puntos de una vez (más eficiente al cerrar sesión).
    points = [{"gbps": 1.2, "jitter_ms": 0.01, "retransmits": 0, "ts": "HH:MM:SS"}, ...]
    """
    if not points:
        return
    conn = get_conn()
    cur  = conn.cursor()
    rows = [
        (session_id, datetime.now(), p["gbps"], p.get("jitter_ms", 0), p.get("retransmits", 0))
        for p in points
    ]
    cur.executemany("""
        INSERT INTO measurements (session_id, measured_at, gbps, jitter_ms, retransmits)
        VALUES (%s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    conn.close()


# ── Consultas de reporte ──────────────────────────────────────────────────────

def get_sessions(limit: int = 50, mode: str = None) -> list[dict]:
    """Lista las últimas sesiones con su resumen."""
    conn = get_conn()
    cur  = conn.cursor(dictionary=True)
    where = "WHERE s.mode = %s" if mode else ""
    params = (mode, limit) if mode else (limit,)
    cur.execute(f"""
        SELECT
            s.id, s.mode, s.host, s.port, s.protocol, s.parallel,
            s.duration_s, s.started_at, s.ended_at, s.status,
            ss.avg_gbps, ss.max_gbps, ss.min_gbps,
            ss.avg_jitter_ms, ss.total_retransmits, ss.total_samples
        FROM sessions s
        LEFT JOIN session_summary ss ON ss.session_id = s.id
        {where}
        ORDER BY s.started_at DESC
        LIMIT %s
    """, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_session_measurements(session_id: int) -> list[dict]:
    """Retorna todos los puntos de una sesión (para graficar histórico)."""
    conn = get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT measured_at, gbps, jitter_ms, retransmits
        FROM measurements
        WHERE session_id = %s
        ORDER BY measured_at ASC
    """, (session_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_summary(session_id: int) -> dict | None:
    """Retorna el resumen de una sesión específica."""
    conn = get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, ss.*
        FROM sessions s
        LEFT JOIN session_summary ss ON ss.session_id = s.id
        WHERE s.id = %s
    """, (session_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row
