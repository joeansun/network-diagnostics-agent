import subprocess

from netdiag.analysis.ping import ping_analysis
from netdiag.os.base import OSAdapter
from netdiag.presentation import format_ping_report
from netdiag.data.ping import PingRecord

def run_ping(host: str, os_adapter: OSAdapter, count: int, timeout_ms: int) -> PingRecord: 
    result = os_adapter.execute_ping(
        host=os_adapter.get_gateway_ip() if host == "gateway" else host, 
        count=count,
        timeout_ms=timeout_ms
    )
    
    return ping_analysis(os_adapter=os_adapter, raw_input=result.stdout)

    


