import subprocess

from netdiag.analysis.ping import ping_analysis
from netdiag.os import get_os_adapter


def run_ping(app_config): 
    os_adapter = get_os_adapter()
    ping_config = app_config.ping

    for host in ping_config.targets:
        result = os_adapter.execute_ping(
            host=os_adapter.get_gateway_ip() if host == "gateway" else host, 
            count=ping_config.count,
            timeout_ms=ping_config.timeout_ms
        )

        print(result.stdout, result.stderr, result.returncode)
        ping_analysis(os_adapter=os_adapter, raw_input=result.stdout)

    


