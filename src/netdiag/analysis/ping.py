import re
import math
import subprocess
from enum import Enum
from netdiag.data.ping import *
from itertools import dropwhile


# class 



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
def diagnose_from_signals(signal: PingSignals) -> DiagnosisCause:
    if signal.no_reply: return DiagnosisCause.NO_CONNECTIVITY
    if signal.high_loss: return DiagnosisCause.HIGH_LOSS
    if signal.unstable_jitter: return DiagnosisCause.UNSTABLE_JITTER
    if signal.high_latency: return DiagnosisCause.HIGH_LATENCY
    return DiagnosisCause.OK

def build_ping_metrics(ping_info: dict) -> PingMetrics:
    sent, received, loss_pct_perc = ping_info["packets_info"]
    rtt_min, rtt_avg, rtt_max, rtt_stddev = ping_info["stats_data"]
    return PingMetrics(
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

def build_ping_signals(ping_metrics: PingMetrics) -> PingSignals:
    return PingSignals(
        no_reply = ping_metrics.received == 0,
        any_loss = ping_metrics.loss_pct_perc > 0.0,
        high_loss = ping_metrics.loss_pct_perc >= HIGH_PACKET_LOSS_THRESHOLD_PCT,
        high_latency = ping_metrics.rtt_avg_ms >= HIGH_LATENCY_THRESHOLD_MS,
        unstable_jitter = ping_metrics.jitter_ratio > UNSTABLE_JITTER,
        unstable = (
            ping_metrics.rtt_stddev_ms >= UNSTABLE_DEVIATION * ping_metrics.rtt_avg_ms
            or (ping_metrics.rtt_max_ms - ping_metrics.rtt_min_ms) >= 100.0
        )
    )

# CAUSE_SUMMARY located in data/ping.py 
def summarise_causes(causes: DiagnosisCause) -> str:
    return CAUSE_SUMMARY.get(causes, "Unknown or unclassified condition.")

def compute_confidence(ping_metrics: PingMetrics, ping_signals: PingSignals, causes: DiagnosisCause) -> float:
    ...

def summarise_evidence() -> dict[str, str]:
    ...

def build_ping_diagnosis(ping_signals: PingSignals) -> PingDiagnosis:
    causes = diagnose_from_signals(ping_signals)
    return PingDiagnosis(
        causes = causes,
        summary = summarise_causes(causes),
        confidence = compute_confidence(),
        evidence = summarise_evidence()
    )

def build_record(ping_info: dict, ping_metrics: PingMetrics, ping_signals: PingSignals, ping_diagnosis: PingDiagnosis) -> PingRecord:
    return PingRecord(
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'),
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        target = ping_info["address"],
        metrics = ping_metrics,
        signals = ping_signals,
        diagnosis = ping_diagnosis
    )

def ping_analysis(raw_input: str) -> None:
    ping_info = parse_ping(raw_input)
    print(ping_info)

    ping_metrics = build_ping_metrics(ping_info)
    ping_signals = build_ping_signals(ping_metrics)
    ping_diagnosis = build_ping_diagnosis(ping_signals)
    ping_record = build_record(ping_info, ping_metrics, ping_signals, ping_diagnosis)

    print(ping_metrics)
    print(ping_signals)
    


command = "ping -c 5 google.com"
result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            shell=True,
        )
print(result.stdout)
print()
ping_analysis(result.stdout)
