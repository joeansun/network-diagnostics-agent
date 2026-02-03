# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Lint and format
ruff check src/
ruff format src/

# Run tests
pytest

# Run CLI commands
netdiag ping              # Run ping probe
netdiag ping -c 10        # Run ping with 10 packets
netdiag run               # Run all configured probes
python -m netdiag ping    # Alternative entry point
```

## Architecture

Network diagnostics tool with a 5-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  CLI Layer (cli.py)                                         │
│  Subcommands: ping, dns, run                                │
├─────────────────────────────────────────────────────────────┤
│  Analysis Layer (analysis/)                                 │
│  Signal detection → Diagnosis inference → Confidence scoring│
├─────────────────────────────────────────────────────────────┤
│  Data Layer (data/)                                         │
│  Dataclasses: ParseResult → Metrics → Signals → Diagnosis   │
├─────────────────────────────────────────────────────────────┤
│  Persistence Layer (database.py)                            │
│  SQLite storage for sessions and probe records              │
├─────────────────────────────────────────────────────────────┤
│  Probes Layer (probes/)                                     │
│  Execute measurements: ping, dns, http, tcp                 │
└─────────────────────────────────────────────────────────────┘
```

Each probe type (ping, dns, etc.) has parallel files across probes/, data/, and analysis/ directories.

## Data Flow Pattern

For each probe type, data flows through a transformation pipeline:

1. **Raw Output** → `parse_*()` → **ParseResult** (raw parsed values)
2. **ParseResult** → `build_*_metrics()` → **Metrics** (computed statistics)
3. **Metrics** → `build_*_signals()` → **Signals** (boolean flags for conditions)
4. **Signals** → `infer_*_diagnosis()` → **Diagnosis** (cause, summary, confidence, evidence)

## Naming Conventions

- `parse_*()` - Parse raw command output
- `build_*()` - Construct derived data structures
- `compute_*()` - Calculate individual metrics
- `summarise_*()` - Aggregate results
- `infer_*()` - Derive diagnosis from signals

## Key Constants (data/ping.py)

Threshold constants that drive signal detection:
- `HIGH_PACKET_LOSS_THRESHOLD_PCT = 5.0`
- `HIGH_LATENCY_THRESHOLD_MS = 150`
- `UNSTABLE_JITTER = 0.25` (ratio of jitter to avg RTT)
- `UNSTABLE_JITTER_ABS_MS = 5.0`

## Configuration

TOML config at `~/.config/netdiag/config.toml` (platform-aware via platformdirs). See `config_example.toml` for structure. Falls back to `DEFAULT_CONFIG` in `config/default.py`.

## Database Persistence

SQLite database stores probe results and session history for analysis and trending:

**Schema:**
- `sessions` table - Tracks command execution sessions with status tracking
- `ping_records` table - Stores complete ping probe data (metrics, signals, diagnosis)

**Key Functions (database.py):**
- `create_db()` - Initialize database schema
- `insert_sessionss_db()` - Create new session record
- `update_session_status_db()` - Update session completion status
- `insert_ping_records_db()` - Store PingRecord with full diagnostic data
- `get_db_connection()` - Context manager for safe connection handling

Database location: `~/.config/netdiag/netdiag.db` (follows XDG Base Directory specification)

Data stored includes:
- Metrics: packet loss, RTT statistics, jitter
- Signals: boolean flags for detected conditions
- Diagnosis: cause, confidence, summary, evidence (JSON)

## Cross-Platform Considerations

- Ping output parsing handles macOS, Linux iputils, and BusyBox variants
- Time format variations: `time=123.45 ms` and `time=(1008).473 ms`
- Gateway detection uses Unix-style `route` command (Windows support pending)

## Dependencies

Zero runtime dependencies. Dev dependencies: ruff, pytest, platformdirs.
