from dataclasses import dataclass
from datetime import datetime
from enum import Enum

HIGH_PACKET_LOSS_THRESHOLD_PCT = 5.0
HIGH_LATENCY_THRESHOLD_MS = 150
UNSTABLE_DEVIATION = 0.30
UNSTABLE_JITTER_ABS_MS = 5.0
UNSTABLE_JITTER = 0.25
UNSTABLE_RTT_SPREAD_MS = 100.0

LOSS_T1 = 15.0
LOSS_T2 = 8.0
LAT_T1 = 400.0
LAT_T2 = 250.0
JIT_R1 = 0.5
JIT_R2 = 0.35
JIT_A1 = 12.0
JIT_A2 = 8.0


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

# This cause evidence fields could be refactored into metrics and reasoning
# in the future if needed as it would be benefit to show multiple signals
# as evidence
# Currently, only metrics are shown
CAUSE_EVIDENCE_FIELDS = {
    DiagnosisCause.OK: ["loss_pct", "rtt_avg_ms", "jitter_ratio"],
    DiagnosisCause.NO_CONNECTIVITY: [
        "sent",
        "received",
        "loss_pct",
    ],
    DiagnosisCause.HIGH_LOSS: [
        "loss_pct",
        "sent",
        "received",
    ],
    DiagnosisCause.UNSTABLE_JITTER: [
        "jitter",
        "jitter_ratio",
        "rtt_avg_ms",
    ],
    DiagnosisCause.HIGH_LATENCY: [
        "rtt_avg_ms",
        "rtt_min_ms",
        "rtt_max_ms",
        "loss_pct",
    ],
}


# for storing ping info in parse_ping function
@dataclass(frozen=True, slots=True)
class PingParseResult:
    address: str
    times_ms: list[float]
    sent: int
    received: int
    loss_pct: float
    rtt_min_ms: float
    rtt_avg_ms: float
    rtt_max_ms: float
    rtt_stddev_ms: float
    jitter: float
    jitter_ratio: float


@dataclass
class PingMetrics:
    sent: int
    received: int
    loss_pct: float
    rtt_min_ms: float
    rtt_avg_ms: float
    rtt_max_ms: float
    rtt_stddev_ms: float
    jitter: float
    jitter_ratio: float


@dataclass
class PingSignals:
    no_reply: bool
    any_loss: bool
    high_loss: bool
    high_latency: bool
    unstable_jitter: bool
    unstable: bool


@dataclass
class PingDiagnosis:
    cause: DiagnosisCause
    summary: str
    confidence: float
    evidence: dict[str, float]


@dataclass
class PingRecord:
    session_id: str
    timestamp: datetime
    target: str
    metrics: PingMetrics
    signals: PingSignals
    diagnosis: PingDiagnosis


class PingParseError(ValueError):
    """Ping output doesn't match the expected format."""

    pass
