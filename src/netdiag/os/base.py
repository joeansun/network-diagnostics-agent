import math
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass

import netdiag.data.ping as ping


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
        """ ""Build the ping command based on the OS specifics."""
        pass

    @abstractmethod
    def execute_ping(
        self, host: str, count: int, timeout_ms: int
    ) -> subprocess.CompletedProcess[str]:
        pass

    @abstractmethod
    def parse_ping(self, raw_input: str) -> ping.PingParseResult:
        """ ""Parse the ping command based on the OS specifics."""
        pass

    @abstractmethod
    def get_gateway_ip(self):
        pass

    @staticmethod
    def compute_jitter(times_ms: list[float]) -> tuple[float, float]:
        ok = [t for t in times_ms if t is not None]
        if len(ok) < 2:
            return 0.0, 0.0

        diffs = [abs(ok[i] - ok[i - 1]) for i in range(1, len(ok))]
        jitter = sum(diffs) / len(diffs)

        rtt_avg = sum(ok) / len(ok)
        jitter_ratio = jitter / max(rtt_avg, 1.0)

        return jitter, jitter_ratio

    @staticmethod
    def compute_std(times_ms: list[float]) -> float:
        ok = [t for t in times_ms if t is not None]
        n = len(ok)
        if n == 0:
            return 0.0
        mean = sum(ok) / n
        var = sum((t - mean) ** 2 for t in ok) / n  # population variance
        return math.sqrt(var)


""""
OSAdapter (ABC)
    ├── WindowsOSAdapter
    └── UnixBaseAdapter (ABC)
        ├── MacOSAdapter
        └── LinuxAdapter
"""
