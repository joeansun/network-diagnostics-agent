from abc import ABC, abstractmethod
from asyncio import subprocess
from .base import OSAdapter
from dataclasses import dataclass

# Abstract class for OS-specific implementations
class UnixAdapter(OSAdapter, ABC):

    @abstractmethod
    def build_ping_command(self, host: str, count: int, timeout_ms: int) -> list[str]:
        """""Build the ping command based on the OS specifics."""
        return [
            "ping",
            "-c", str(count),      # Count flag
            "-W", str(timeout_ms), # Timeout flag (milliseconds)
            host
        ]

    def execute_ping(self, host: str, count: int, timeout_ms: int) -> subprocess.CompletedProcess[str]:
        cmd = self.build_ping_command(host, count, timeout_ms)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

    @abstractmethod
    def parse_ping_output(self):
        """""Parse the ping command based on the OS specifics."""
        pass

    def get_gateway_ip(self):
        result = subprocess.run(
                    ["route", "-n", "get", "default"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
        for line in result.stdout.splitlines():
            stripped_line = line.lstrip()
            if stripped_line.startswith("gateway"):
                return stripped_line.split(":", 1)[1].strip()
            
        raise ValueError("Gateway IP not found")




    
