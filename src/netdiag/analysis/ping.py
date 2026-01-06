import re
import subprocess
from enum import Enum
from netdiag.data.ping import *
from itertools import dropwhile

class DiagnosisCause(str, Enum):
    OK = "ok"



def parse_ping(raw_input: str) -> dict:
    ping_info = dict()
    splitted_inputs = raw_input.splitlines()

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

    
    return ping_info 

def ping_anaylsis(raw_input: str) -> None:
    ping_info = parse_ping(raw_input)
    print(ping_info)

    ping_metrics = PingMetrics(
        sent=int(ping_info["packets_info"][0]),
        received=int(ping_info["packets_info"][1]),
        loss_pct_perc=float(ping_info["packets_info"][2]),
        rtt_min_ms=ping_info["stats_data"][0],
        rtt_avg_ms=ping_info["stats_data"][1],
        rtt_max_ms=ping_info["stats_data"][2],
        rtt_stddev_ms=ping_info["stats_data"][3]
    )

    ping_signals = PingSignals(
        high_loss=ping_metrics.loss_pct_perc >= HIGH_PACKET_LOSS_THRESHOLD_PCT,
        high_latency=ping_metrics.rtt_avg_ms >= HIGH_LATENCY_THRESHOLD_MS,
        unstable=(
            ping_metrics.rtt_stddev_ms >= UNSTABLE_DEVIATION * ping_metrics.rtt_avg_ms
            or (ping_metrics.rtt_max_ms - ping_metrics.rtt_min_ms) >= 100.0
        )
        
    )

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
ping_anaylsis(result.stdout)
