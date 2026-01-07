import re
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

    # calcualte jitter
    abs_std = [abs(value - ping_info["stats_data"][1]) for value in time_each_run]
    print(ping_info["stats_data"][1])
    print(abs_std)
    print(sum(abs_std))

    
    return ping_info 

def ping_anaylsis(raw_input: str) -> None:
    ping_info = parse_ping(raw_input)
    print(ping_info)

    # ping_metrics = PingMetrics(
    #     sent=int(ping_info["packets_info"][0]),
    #     received=int(ping_info["packets_info"][1]),
    #     loss_pct_perc=float(ping_info["packets_info"][2]),
    #     rtt_min_ms=ping_info["stats_data"][0],
    #     rtt_avg_ms=ping_info["stats_data"][1],
    #     rtt_max_ms=ping_info["stats_data"][2],
    #     rtt_stddev_ms=ping_info["stats_data"][3]
    # )

    # ping_signals = PingSignals(
    #     no_reply=ping_metrics.received == 0,
    #     any_loss=ping_metrics.sent - ping_metrics.received > 0,
    #     high_loss=ping_metrics.loss_pct_perc >= HIGH_PACKET_LOSS_THRESHOLD_PCT,
    #     high_latency=ping_metrics.rtt_avg_ms >= HIGH_LATENCY_THRESHOLD_MS,
    #     unstable=(
    #         ping_metrics.rtt_stddev_ms >= UNSTABLE_DEVIATION * ping_metrics.rtt_avg_ms
    #         or (ping_metrics.rtt_max_ms - ping_metrics.rtt_min_ms) >= 100.0
    #     )
    # )

    # ping_diagnosis = PingDiagnosis(
    #     causes : str
    #     summary : str
    #     confidence : float
    #     evidence : dict[str, float]
    # )

    # ping_record = PingRecord(
    #     run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'),
    #     timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    #     target=ping_info["address"],
    #     metrics=ping_metrics,
    #     signals=ping_signals,
    #     diagnosis=ping_diagnosis
    # )



    # print(ping_metrics)
    # print(ping_signals)
    


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
