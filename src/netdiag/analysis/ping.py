import re
import subprocess
from itertools import dropwhile


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
    ping_info["packets_info"] = packets_info

    # min / avg / max / stddev 
    m = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", next(result))
    if not m:
        raise ValueError("Could not parse stats")
    ping_info["stats_data"] = m.groups()

    
    return ping_info 

def ping_anaylsis(raw_input: str) -> None:
    ping_info = parse_ping(raw_input)
    print(ping_info)


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
