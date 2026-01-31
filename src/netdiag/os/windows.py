from .base import OSAdapter
import subprocess
import re

class WindowsOSAdapter(OSAdapter):
    def build_ping_command(self, host: str, count: int, timeout_ms: int) -> subprocess.CompletedProcess[str]:
        return [
            "ping", 
            host,
            "-n", str(count),
            "-w", str(timeout_ms)
        ]
    
    def parse_ping_output(self):
        pass

    def get_gateway_ip(self):
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            if "Default Gateway" in line:
                return line.split(":", 1)[1].strip()
            
        raise ValueError("Gateway IP not found")
