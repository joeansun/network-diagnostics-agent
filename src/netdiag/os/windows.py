import re
import subprocess

import netdiag.data.ping as ping

from .base import OSAdapter

_TIME_RE_WINDOWS = re.compile(r"\btime[=<]\s*(?P<ms>\d+(?:\.\d+)?)\s*ms\b", re.IGNORECASE)
_ADDR_RE_WINDOWS = re.compile(r"^Ping statistics for (?P<addr>.+?):$", re.IGNORECASE)
_PACKET_RE_WINDOWS = re.compile(
    r"Packets:\s+Sent\s*=\s*(?P<tx>\d+),\s*"
    r"Received\s*=\s*(?P<rx>\d+),\s*"
    r"Lost\s*=\s*\d+\s*\((?P<loss>\d+(?:\.\d+)?)%\s+loss\)",
    re.IGNORECASE,
)
_RTT_RE_WINDOWS = re.compile(
    r"Minimum\s*=\s*(?P<min>\d+(?:\.\d+)?)ms,\s*"
    r"Maximum\s*=\s*(?P<max>\d+(?:\.\d+)?)ms,\s*"
    r"Average\s*=\s*(?P<avg>\d+(?:\.\d+)?)ms",
    re.IGNORECASE,
)


class WindowsOSAdapter(OSAdapter):
    def build_ping_command(
        self, host: str, count: int, timeout_ms: int
    ) -> subprocess.CompletedProcess[str]:
        return ["ping", host, "-n", str(count), "-w", str(timeout_ms)]

    def execute_ping(
        self, host: str, count: int, timeout_ms: int
    ) -> subprocess.CompletedProcess[str]:
        """ "Shared Across all platforms"""
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
            m = _TIME_RE_WINDOWS.search(ln)
            if m:
                raw = m.group("ms")
                ms = float(raw.replace("(", "").replace(")", ""))
                times_ms.append(ms)

        # Parse the address from the header
        header = next((m for ln in lines if (m := _ADDR_RE_WINDOWS.search(ln))), None)
        if not header:
            raise ping.PingParseError("missing ping statistics header")

        addr = header.group("addr")

        # Parse the packet information
        packets = next((m for ln in lines if (m := _PACKET_RE_WINDOWS.search(ln))), None)
        if not packets:
            raise ping.PingParseError("missing packets summary line")

        sent = int(packets.group("tx"))
        received = int(packets.group("rx"))
        loss_pct = float(packets.group("loss"))

        # Parse the RTT stats
        rtt = next((m for ln in lines if (m := _RTT_RE_WINDOWS.search(ln))), None)
        if rtt:
            rtt_min = float(rtt.group("min"))
            rtt_avg = float(rtt.group("avg"))
            rtt_max = float(rtt.group("max"))
        else:
            if received == 0:
                # Policy: if no replies, allow RTT fields = 0.0
                rtt_min = rtt_avg = rtt_max = rtt_std = 0.0
            else:
                raise ping.PingParseError("missing rtt stats line despite receiving replies")

        rtt_std = self.compute_std(times_ms=times_ms)

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
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=False,
        )

        for line in result.stdout.splitlines():
            if "Default Gateway" in line:
                return line.split(":", 1)[1].strip()

        raise ValueError("Gateway IP not found")
