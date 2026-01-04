from dataclasses import dataclass
from datetime import timezone, datetime

@dataclass
class PingMetrics:
    sent : int
    received : int
    loss_pct : int
    rtt_min_ms : int
    rtt_avg_ms : int
    rtt_max_ms : int

@dataclass
class PingSignals:
    high_loss : bool
    high_latency : bool
    unstable : bool
    
@dataclass
class PingDiagnosis:
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
