import re
import subprocess
from itertools import dropwhile


def parse_ping(raw_input: str) -> str:
    splitted_inputs = raw_input.splitlines()

    # extract the statistics for ping 
    result = dropwhile(lambda line: "statistics" not in line, splitted_inputs)

    # extract the address or hostname from the statistics title
    address = re.search(r"^---\s([A-Za-z0-9][A-Za-z0-9.-]*)\s", next(result)).group(1)

    # extract the info about packet transmission
    packets_info = next(result).split(", ")

    # min / avg / max / stddev 
    stats_data = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", next(result)).groups()

def ping_anaylsis(raw_input: str) -> None:
    return


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
parse_ping(result.stdout)
