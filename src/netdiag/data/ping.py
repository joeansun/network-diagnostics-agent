from dataclasses import dataclass
from datetime import timezone, datetime
from enum import Enum

HIGH_PACKET_LOSS_THRESHOLD_PCT = 5.0
HIGH_LATENCY_THRESHOLD_MS = 150
UNSTABLE_DEVIATION = 0.30
UNSTABLE_JITTER_ABS_MS = 5.0
UNSTABLE_JITTER = 0.25

LOSS_T1=15.0; LOSS_T2=8.0
LAT_T1=400.0; LAT_T2=250.0
JIT_R1=0.5; JIT_R2=0.35
JIT_A1=12.0;  JIT_A2=8.0


class DiagnosisCause(str, Enum):
    OK = "ok"
    NO_CONNECTIVITY = "no_connectivity"
    HIGH_LOSS = "high_loss"
    UNSTABLE_JITTER = "unstable_jitter"
    HIGH_LATENCY = "high_latency"

CAUSE_SUMMARY = {
    DiagnosisCause.NO_CONNECTIVITY: "No connectivity detected.",
    DiagnosisCause.HIGH_LOSS: "Packet loss is high.",
    DiagnosisCause.UNSTABLE_JITTER: "Connection is unstable (high jitter).",
    DiagnosisCause.HIGH_LATENCY: "Latency is high.",
    DiagnosisCause.OK: "Connection appears normal.",
}

@dataclass
class PingMetrics:
    sent : int
    received : int
    loss_pct_perc : float
    rtt_min_ms : float
    rtt_avg_ms : float
    rtt_max_ms : float
    rtt_stddev_ms : float
    jitter : float
    jitter_ratio : float

@dataclass
class PingSignals:
    no_reply : bool
    any_loss : bool
    high_loss : bool
    high_latency : bool
    unstable_jitter : bool
    unstable : bool
    
@dataclass
class PingDiagnosis:
    cause : DiagnosisCause
    summary : str
    confidence : float
    evidence : dict[str, float]

@dataclass
class PingRecord:
    run_id : str
    timestamp : datetime
    target : str
    metrics: PingMetrics
    signals: PingSignals
    diagnosis: PingDiagnosis