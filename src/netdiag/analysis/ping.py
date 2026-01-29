
import re
import subprocess
import netdiag.data.ping as ping
from enum import Enum
from datetime import datetime, timezone
from itertools import dropwhile


# 64 bytes from 142.251.46.174: icmp_seq=3 ttl=107 time=(1008).473 ms
# 64 bytes from 142.251.46.174: icmp_seq=4 ttl=107 time=943.241 ms

_TIME_RE = re.compile(r"\btime[=<]\s*(?P<ms>\d+(?:\.\d+)?)\s*ms\b", re.IGNORECASE)


# --- google.com ping statistics ---
_ADDR_RE = re.compile(r"^---\s+(?P<addr>.+?)\s+ping statistics\s+---$", re.IGNORECASE)

# Packet line variants:
# macOS: "5 packets transmitted, 5 packets received, 0.0% packet loss"
# iputils: "5 packets transmitted, 5 received, 0% packet loss, time 4006ms"
# BusyBox: "5 packets transmitted, 4 packets received, 20% packet loss"
_PACKET_RE = re.compile(r"(?P<tx>\d+)\s+packets transmitted,\s+" 
                       r"(?P<rx>\d+)\s+(?:packets\s+)?received,\s+" 
                       r"(?P<loss>\d+(?:\.\d+)?)%\s+packet loss",
                       re.IGNORECASE)

# macOS: "round-trip min/avg/max/stddev = ... ms"
# Linux: "rtt min/avg/max/mdev = ... ms"
_RTT_RE = re.compile(
    r"(?:round-trip|rtt)\s+min/avg/max/(?:stddev|mdev)\s*=\s*"
    r"(?P<min>\d+(?:\.\d+)?)/(?P<avg>\d+(?:\.\d+)?)/(?P<max>\d+(?:\.\d+)?)/(?P<std>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def PingParseError(ValueError):
    """Ping output doesn't match the expected format."""

def parse_ping(raw_input: str) -> ping.PingParseResult:
    lines = [ln.strip() for ln in raw_input.splitlines() if ln.strip()]
    if not lines: 
        raise PingParseError("empty ping output")

    # Parse time for each reply from icmp
    times_ms: list[float] = []
    for ln in lines:
        m = _TIME_RE.search(ln)
        if m: 
            times_ms.append(float(m.group("ms")))

    # Parse the address from the header 
    header = next((m for ln in lines if (m := _ADDR_RE.search(ln))), None)
    if not header:
        raise PingParseError("missing '--- <address> ping statistics ---' header")

    addr = header.group("addr")

    # Parse the packet information 
    packets = next((m for ln in lines if (m := _PACKET_RE.search(ln))), None)
    if not packets:
        raise PingParseError("missing packets summary line")
    
    sent = int(packets.group("tx"))
    received = int(packets.group("rx"))
    loss_pct = float(packets.group("loss"))

    # Parse the RTT stats
    rtt = next((m for ln in lines if (m := _RTT_RE.search(ln))), None)
    if rtt:
        rtt_min = float(rtt.group("min"))
        rtt_avg = float(rtt.group("avg"))
        rtt_max = float(rtt.group("max"))
        rtt_std = float(rtt.group("std"))
    else:
        if received == 0:
            # Policy: if no replies, allow RTT fields = 0.0
            rtt_min = rtt_avg = rtt_max = rtt_std = 0.0
        else:
            raise PingParseError("missing rtt stats line despite receiving replies")

    




    return PingParseResult(
        address = addr,
        times_ms = times_ms, 
        sent = sent, 
        received = received, 
        loss_pck = loss_pct,
        rtt_min_ms = rtt_min,
        rtt_avg_ms = rtt_avg,
        rtt_max_ms = rtt_max,
        rtt_stddev_ms = rtt_std,
        jitter_ms = 
        jitter_ratio = 
    )



def parse_ping(raw_input: str) -> dict:
    ping_info = dict()
    splitted_inputs = raw_input.splitlines()

    # extract time for each run into a list
    pattern = re.compile(r"time=([\d.]+) ms$")
    time_each_run = [
        float(m.group(1))
        for line in splitted_inputs
        if (m := pattern.search(line))
    ]
    ping_info["time_each_run"] = time_each_run


    # extract the statistics for ping 
    result = dropwhile(lambda line: "statistics" not in line, splitted_inputs)

    # extract the address or hostname from the statistics title
    m = re.search(r"^---\s([A-Za-z0-9][A-Za-z0-9.-]*)\s", next(result))
    if not m:
        raise ValueError("Could not parse address")
    ping_info["address"] = m.group(1)

    # extract the info about packet transmission
    packets_info = next(result).split(", ")
    packets_number = [re.search(r"^[\d.]+", s).group(0) for s in packets_info]
    ping_info["packets_info"] = packets_number

    # min / avg / max / stddev 
    m = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", next(result))
    if not m:
        raise ValueError("Could not parse stats")
    stats_data_group = [float(s) for s in m.groups()]
    ping_info["stats_data"] = stats_data_group

    # calcualte jitter, jitter_ratio
    if len(time_each_run) < 2:
        ping_info["jitter"] = 0.0
        ping_info["jitter_ratio"] = 0.0
    else:
        average_delay = ping_info["stats_data"][1]
        sum_of_squared_difference = sum([(value - average_delay) ** 2 for value in time_each_run])
        jitter = math.sqrt(sum_of_squared_difference / len(time_each_run))
        ping_info["jitter"] = jitter
        ping_info["jitter_ratio"] =  jitter / average_delay
    
    return ping_info 

# DiagnosisCause located in data/ping.py
def diagnose_from_signals(signal: ping.PingSignals) -> ping.DiagnosisCause:
    if signal.no_reply: return ping.DiagnosisCause.NO_CONNECTIVITY
    if signal.high_loss: return ping.DiagnosisCause.HIGH_LOSS
    if signal.unstable_jitter: return ping.DiagnosisCause.UNSTABLE_JITTER
    if signal.high_latency: return ping.DiagnosisCause.HIGH_LATENCY
    return ping.DiagnosisCause.OK

def build_ping_metrics(ping_info: dict) -> ping.PingMetrics:
    sent, received, loss_pct_perc = ping_info["packets_info"]
    rtt_min, rtt_avg, rtt_max, rtt_stddev = ping_info["stats_data"]
    return ping.PingMetrics(
        sent = int(sent),
        received = int(received),
        loss_pct_perc = float(loss_pct_perc),
        rtt_min_ms = rtt_min,
        rtt_avg_ms = rtt_avg,
        rtt_max_ms = rtt_max,
        rtt_stddev_ms = rtt_stddev,
        jitter = ping_info["jitter"],
        jitter_ratio = ping_info["jitter_ratio"]
    )

def build_ping_signals(ping_metrics: ping.PingMetrics) -> ping.PingSignals:
    return ping.PingSignals(
        no_reply = ping_metrics.received == 0,
        any_loss = ping_metrics.loss_pct_perc > 0.0,
        high_loss = ping_metrics.loss_pct_perc >= ping.HIGH_PACKET_LOSS_THRESHOLD_PCT,
        high_latency = ping_metrics.rtt_avg_ms >= ping.HIGH_LATENCY_THRESHOLD_MS,

        # unstable jitter must satisfy both conditions so fewer false alert
        unstable_jitter = ping_metrics.jitter_ratio >= ping.UNSTABLE_JITTER and ping_metrics.jitter >= ping.UNSTABLE_JITTER_ABS_MS,
        unstable = (
            ping_metrics.rtt_stddev_ms >= ping.UNSTABLE_DEVIATION * ping_metrics.rtt_avg_ms
            or (ping_metrics.rtt_max_ms - ping_metrics.rtt_min_ms) >= 100.0
        )
    )

# CAUSE_SUMMARY located in data/ping.py 
def summarise_causes(cause: ping.DiagnosisCause) -> str:
    return ping.CAUSE_SUMMARY.get(cause, "Unknown or unclassified condition.")

# confidence is a value between [0.0, 1.0], 1.0 represents very cause
def compute_confidence(ping_metrics: ping.PingMetrics, ping_signals: ping.PingSignals, cause: ping.DiagnosisCause) -> float:
    if cause == ping.DiagnosisCause.NO_CONNECTIVITY:
        cfd_value = 1.0
    elif cause == ping.DiagnosisCause.HIGH_LOSS:
        # Precondition: loss_pct >= 5.0
        if ping_metrics.loss_pct_perc >= ping.LOSS_T1:
            cfd_value = 0.95
        elif ping_metrics.loss_pct_perc >= ping.LOSS_T2:
            cfd_value = 0.85
        else:
            cfd_value = 0.70
    elif cause == ping.DiagnosisCause.UNSTABLE_JITTER:
        # Precondition: jitter_ratio >= 0.25 and jitter > 5 ms
        if ping_metrics.jitter_ratio >= ping.JIT_R1 and ping_metrics.jitter >= ping.JIT_A1:
            cfd_value = 0.95
        elif ping_metrics.jitter_ratio >= ping.JIT_R2 and ping_metrics.jitter >= ping.JIT_A2:
            cfd_value = 0.85
        else:
            cfd_value = 0.70
    elif cause == ping.DiagnosisCause.HIGH_LATENCY:
        # Precondition: rtt_avg_ms >= 150 ms
        if ping_metrics.rtt_avg_ms >= ping.LAT_T1:
            cfd_value = 0.95
        elif ping_metrics.rtt_avg_ms >= ping.LAT_T2:
            cfd_value = 0.85
        else:
            cfd_value = 0.70
    elif cause == ping.DiagnosisCause.OK:
        cfd_value = 1.0

    else:
        cfd_value = 0.5

    if ping_metrics.sent < 20 and cause not in (ping.DiagnosisCause.OK, ping.DiagnosisCause.NO_CONNECTIVITY):
        cfd_value = max(0.30, cfd_value - 0.20)

    return min(1.0, max(0.0, cfd_value))


def summarise_evidence(ping_metrics: ping.PingMetrics, cause: ping.DiagnosisCause) -> dict[str, float]:
    evidence = {}
    for field in ping.CAUSE_EVIDENCE_FIELDS[cause]:
        evidence[field] = getattr(ping_metrics, field)

    return evidence

def build_ping_diagnosis(ping_metrics: ping.PingMetrics, ping_signals: ping.PingSignals) -> ping.PingDiagnosis:
    cause = diagnose_from_signals(ping_signals)
    return ping.PingDiagnosis(
        cause = cause,
        summary = summarise_causes(cause),
        confidence = compute_confidence(ping_metrics, ping_signals, cause),
        evidence = summarise_evidence(ping_metrics, cause)
    )

def build_record(ping_info: dict, ping_metrics: ping.PingMetrics, ping_signals: ping.PingSignals, ping_diagnosis: ping.PingDiagnosis) -> ping.PingRecord:
    now = ping.datetime.now(ping.timezone.utc)
    return ping.PingRecord(
        run_id = now.strftime('%Y%m%dT%H%M%S%fZ'),
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        target = ping_info["address"],
        metrics = ping_metrics,
        signals = ping_signals,
        diagnosis = ping_diagnosis
    )

def ping_analysis(raw_input: str) -> ping.PingRecord:
    ping_info = parse_ping(raw_input)

    ping_metrics = build_ping_metrics(ping_info)
    ping_signals = build_ping_signals(ping_metrics)
    ping_diagnosis = build_ping_diagnosis(ping_metrics, ping_signals)
    ping_record = build_record(ping_info, ping_metrics, ping_signals, ping_diagnosis)

    return ping_record