import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from netdiag.data.ping import PingRecord


@contextmanager
def get_db_connection(db_path: Path):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def create_db(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY, 
            command TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT NOT NULL
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS ping_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            target TEXT NOT NULL,
            
            -- Metrics
            sent INTEGER,
            received INTEGER,
            loss_pct REAL,
            rtt_min_ms REAL,
            rtt_avg_ms REAL,
            rtt_max_ms REAL,
            rtt_stddev_ms REAL,
            jitter REAL,
            jitter_ratio REAL,
            
            -- Signals 
            no_reply BOOLEAN,
            any_loss BOOLEAN,
            high_loss BOOLEAN,
            high_latency BOOLEAN,
            unstable_jitter BOOLEAN,
            unstable BOOLEAN,
            
            -- Diagnosis
            diagnosis_cause TEXT,
            diagnosis_confidence REAL,
            diagnosis_summary TEXT,
            diagnosis_evidence TEXT,  -- JSON string
            
            FOREIGN KEY (run_id) REFERENCES probe_runs(run_id)
        );
    ''')

def insert_ping_records_db(*, 
                           run_id: str, 
                           ping_record: PingRecord, 
                           conn: sqlite3.Connection) -> None:
    conn.execute('''
        INSERT INTO ping_records (
            run_id, timestamp, target,
            sent, received, loss_pct, rtt_min_ms, rtt_avg_ms, rtt_max_ms, rtt_stddev_ms,
            jitter, jitter_ratio,
            no_reply, any_loss, high_loss, high_latency, unstable_jitter, unstable,
            diagnosis_cause, diagnosis_confidence, diagnosis_summary, diagnosis_evidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        run_id, 
        ping_record.timestamp,
        ping_record.target,
        # Metrics
        ping_record.metrics.sent,
        ping_record.metrics.received,
        ping_record.metrics.loss_pct,
        ping_record.metrics.rtt_min_ms,
        ping_record.metrics.rtt_avg_ms,
        ping_record.metrics.rtt_max_ms,
        ping_record.metrics.rtt_stddev_ms,
        ping_record.metrics.jitter,
        ping_record.metrics.jitter_ratio,
        # Signals (all 6 fields from PingSignals)
        int(ping_record.signals.no_reply),
        int(ping_record.signals.any_loss),
        int(ping_record.signals.high_loss),
        int(ping_record.signals.high_latency),
        int(ping_record.signals.unstable_jitter),
        int(ping_record.signals.unstable),
        # Diagnosis
        ping_record.diagnosis.cause.value, 
        ping_record.diagnosis.confidence,
        ping_record.diagnosis.summary,
        json.dumps(ping_record.diagnosis.evidence) 
    ))
    
    conn.commit()