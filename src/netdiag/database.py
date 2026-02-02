import sqlite3


conn = sqlite3.connect('network_diagnostics.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        target_address TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ping_sessions (
        ping_session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ping_metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ping_session_id INTEGER NOT NULL,
        sent INTEGER, 
        received INTEGER,
        loss_pct REAL,
        rtt_min_ms REAL,
        rtt_avg_ms REAL,
        rtt_max_ms REAL,
        rtt_stddev_ms REAL,
        jitter REAL,
        jitter_ratio REAL,
        FOREIGN KEY (ping_session_id) REFERENCES ping_sessions(ping_session_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ping_signals (
        signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_id INTEGER NOT NULL,
        no_reply BOOLEAN,
        any_loss BOOLEAN,
        high_loss BOOLEAN,
        high_latency BOOLEAN,
        unstable_jitter BOOLEAN,
        unstable BOOLEAN,
        FOREIGN KEY (metric_id) REFERENCES ping_metrics(metric_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ping_diagnoses (
        diagnosis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id INTEGER NOT NULL,
        cause TEXT,
        summary TEXT,
        confidence REAL,
        evidence TEXT,
        FOREIGN KEY (signal_id) REFERENCES ping_signals(signal_id)
    )
''')
