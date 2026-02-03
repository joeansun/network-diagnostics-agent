from netdiag.analysis.ping import ping_analysis
from netdiag.data.ping import PingRecord
from netdiag.os.base import OSAdapter


def run_ping(host: str, 
             os_adapter: OSAdapter, 
             count: int, 
             timeout_ms: int, 
             run_id: str) -> PingRecord:
    result = os_adapter.execute_ping(
        host=os_adapter.get_gateway_ip() if host == "gateway" else host,
        count=count,
        timeout_ms=timeout_ms,
    )

    return ping_analysis(os_adapter=os_adapter, raw_input=result.stdout, run_id=run_id)
