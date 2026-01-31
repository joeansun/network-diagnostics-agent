from abc import ABC, abstractmethod
from dataclasses import dataclass
import subprocess

@dataclass
class PingCommand:
    cmd: list[str]
    # Due to the different flags used by variouis OSes
    timeout_flag: str  
    count_flag: str

# Abstract class for OS-specific implementations
class OSAdapter(ABC):

    @abstractmethod
    def build_ping_command(self, host: str, count: int, timeout_ms: int) -> list[str]:
        """""Build the ping command based on the OS specifics."""
        pass

    def execute_ping(self, host: str, count: int, timeout_ms: int) -> subprocess.CompletedProcess[str]:
        """"Shared Across all platforms"""
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

    @abstractmethod
    def get_gateway_ip(self):
        pass



""""
OSAdapter (ABC)
    ├── WindowsOSAdapter
    └── UnixBaseAdapter (ABC)
        ├── MacOSAdapter
        └── LinuxAdapter
"""
    
    