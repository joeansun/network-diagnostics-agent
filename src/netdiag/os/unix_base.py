import re
import subprocess
from abc import ABC, abstractmethod

import netdiag.data.ping as ping

from .base import OSAdapter

# Unix-specific regex patterns for ping output parsing
_TIME_RE_UNIX = re.compile(r"\btime[=<]\s*(?P<ms>[\d().]+)\s*ms\b", re.IGNORECASE)

_ADDR_RE_UNIX = re.compile(r"^---\s+(?P<addr>.+?)\s+ping statistics\s+---$", re.IGNORECASE)

_PACKET_RE_UNIX = re.compile(
    r"(?P<tx>\d+)\s+packets transmitted,\s+"
    r"(?P<rx>\d+)\s+(?:packets\s+)?received,\s+"
    r"(?P<loss>\d+(?:\.\d+)?)%\s+packet loss",  # ← Fixed: \. not .
    re.IGNORECASE,
)

_RTT_RE_UNIX = re.compile(
    r"(?:round-trip|rtt)\s+min/avg/max/(?:stddev|mdev)\s*=\s*"
    r"(?P<min>\d+(?:\.\d+)?)/(?P<avg>\d+(?:\.\d+)?)/(?P<max>\d+(?:\.\d+)?)/(?P<std>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


# Abstract class for OS-specific implementations
class UnixAdapter(OSAdapter, ABC):
    @abstractmethod
    def build_ping_command(self, host: str, count: int, timeout_ms: int) -> list[str]:
        """ ""Build the ping command based on the OS specifics."""
        return [
            "ping",
            "-c",
            str(count),  # Count flag
            "-W",
            str(timeout_ms),  # Timeout flag (milliseconds)
            host,
        ]

    def execute_ping(
        self, host: str, count: int, timeout_ms: int
    ) -> subprocess.CompletedProcess[str]:
        cmd = self.build_ping_command(host=host, count=count, timeout_ms=timeout_ms)
        return subprocess.run(cmd, capture_output=True, text=True)

    def parse_ping(self, raw_input: str) -> ping.PingParseResult:
        """ ""Parse the ping command based on the OS specifics."""
        lines = [ln.strip() for ln in raw_input.splitlines() if ln.strip()]
        if not lines:
            raise ping.PingParseError("empty ping output")

        # Parse time for each reply from icmp
        times_ms: list[float] = []
        for ln in lines:
            m = _TIME_RE_UNIX.search(ln)
            if m:
                raw = m.group("ms")
                ms = float(raw.replace("(", "").replace(")", ""))
                times_ms.append(ms)

        # Parse the address from the header
        header = next((m for ln in lines if (m := _ADDR_RE_UNIX.search(ln))), None)
        if not header:
            raise ping.PingParseError("missing ping statistics header")

        addr = header.group("addr")

        # Parse the packet information
        packets = next((m for ln in lines if (m := _PACKET_RE_UNIX.search(ln))), None)
        if not packets:
            raise ping.PingParseError("missing packets summary line")

        sent = int(packets.group("tx"))
        received = int(packets.group("rx"))
        loss_pct = float(packets.group("loss"))

        # Parse the RTT stats
        rtt = next((m for ln in lines if (m := _RTT_RE_UNIX.search(ln))), None)
        if rtt:
            rtt_min = float(rtt.group("min"))
            rtt_avg = float(rtt.group("avg"))
            rtt_max = float(rtt.group("max"))
            rtt_std = float(rtt.group("std"))
        else:
            if received == 0:
                # Policy: if no replies, allow RTT fields = 0.0
                rtt_min = rtt_avg = rtt_max = rtt_std = 0.0
            else:
                raise ping.PingParseError("missing rtt stats line despite receiving replies")

        # Parse jitter and jitter_ratio
        jitter, jitter_ratio = self.compute_jitter(times_ms)

        return ping.PingParseResult(
            address=addr,
            times_ms=times_ms,
            sent=sent,
            received=received,
            loss_pct=loss_pct,
            rtt_min_ms=rtt_min,
            rtt_avg_ms=rtt_avg,
            rtt_max_ms=rtt_max,
            rtt_stddev_ms=rtt_std,
            jitter=jitter,
            jitter_ratio=jitter_ratio,
        )

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
