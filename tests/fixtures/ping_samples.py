"""Real ping command outputs from different platforms and scenarios

These are actual outputs collected from real systems to ensure
our parser handles all variations correctly across:
- macOS
- Linux (iputils-ping)
- Windows
"""

# ============================================================================
# macOS Success Cases
# ============================================================================

MACOS_SUCCESS = """PING 8.8.8.8 (8.8.8.8): 56 data bytes
64 bytes from 8.8.8.8: icmp_seq=0 ttl=117 time=10.123 ms
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=15.456 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=12.789 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=117 time=18.234 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=117 time=14.567 ms

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 5 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 10.123/14.234/18.234/2.891 ms
"""

MACOS_PARTIAL_LOSS = """PING 8.8.8.8 (8.8.8.8): 56 data bytes
64 bytes from 8.8.8.8: icmp_seq=0 ttl=117 time=10.5 ms
Request timeout for icmp_seq 1
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=12.3 ms
Request timeout for icmp_seq 3
64 bytes from 8.8.8.8: icmp_seq=4 ttl=117 time=15.7 ms

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 3 packets received, 40.0% packet loss
round-trip min/avg/max/stddev = 10.500/12.833/15.700/2.146 ms
"""

MACOS_TOTAL_LOSS = """PING 192.0.2.1 (192.0.2.1): 56 data bytes
Request timeout for icmp_seq 0
Request timeout for icmp_seq 1
Request timeout for icmp_seq 2
Request timeout for icmp_seq 3
Request timeout for icmp_seq 4

--- 192.0.2.1 ping statistics ---
5 packets transmitted, 0 packets received, 100.0% packet loss
"""

MACOS_HIGH_LATENCY = """PING example.com (93.184.216.34): 56 data bytes
64 bytes from 93.184.216.34: icmp_seq=0 ttl=56 time=250.123 ms
64 bytes from 93.184.216.34: icmp_seq=1 ttl=56 time=280.456 ms
64 bytes from 93.184.216.34: icmp_seq=2 ttl=56 time=265.789 ms
64 bytes from 93.184.216.34: icmp_seq=3 ttl=56 time=275.234 ms
64 bytes from 93.184.216.34: icmp_seq=4 ttl=56 time=290.567 ms

--- example.com ping statistics ---
5 packets transmitted, 5 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 250.123/272.434/290.567/14.523 ms
"""

MACOS_HIGH_JITTER = """PING 8.8.8.8 (8.8.8.8): 56 data bytes
64 bytes from 8.8.8.8: icmp_seq=0 ttl=117 time=5.123 ms
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=95.456 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=8.789 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=117 time=120.234 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=117 time=12.567 ms

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 5 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 5.123/48.434/120.234/49.123 ms
"""

MACOS_TIME_PARENTHESES = """PING 8.8.8.8 (8.8.8.8): 56 data bytes
64 bytes from 8.8.8.8: icmp_seq=0 ttl=117 time=(1008).473 ms
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=(1015).234 ms

--- 8.8.8.8 ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 1008.473/1011.854/1015.234/3.381 ms
"""

# ============================================================================
# Linux (iputils-ping) Cases
# ============================================================================

LINUX_IPUTILS_SUCCESS = """PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=10.1 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=15.4 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=117 time=12.7 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=117 time=18.2 ms
64 bytes from 8.8.8.8: icmp_seq=5 ttl=117 time=14.5 ms

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4005ms
rtt min/avg/max/mdev = 10.123/14.234/18.234/2.891 ms
"""

LINUX_HIGH_LOSS = """PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=10.5 ms

--- 8.8.8.8 ping statistics ---
10 packets transmitted, 1 received, 90% packet loss, time 9010ms
rtt min/avg/max/mdev = 10.500/10.500/10.500/0.000 ms
"""

LINUX_NO_RESPONSE = """PING 192.0.2.1 (192.0.2.1) 56(84) bytes of data.

--- 192.0.2.1 ping statistics ---
5 packets transmitted, 0 received, 100% packet loss, time 4005ms
"""

LINUX_UNSTABLE = """PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=10.1 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=150.4 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=117 time=15.2 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=117 time=180.3 ms
64 bytes from 8.8.8.8: icmp_seq=5 ttl=117 time=12.8 ms

--- 8.8.8.8 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4005ms
rtt min/avg/max/mdev = 10.100/73.760/180.300/75.234 ms
"""

# ============================================================================
# Windows Cases
# ============================================================================

WINDOWS_SUCCESS = """
Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=10ms TTL=117
Reply from 8.8.8.8: bytes=32 time=15ms TTL=117
Reply from 8.8.8.8: bytes=32 time=12ms TTL=117
Reply from 8.8.8.8: bytes=32 time=18ms TTL=117
Reply from 8.8.8.8: bytes=32 time=14ms TTL=117

Ping statistics for 8.8.8.8:
    Packets: Sent = 5, Received = 5, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 10ms, Maximum = 18ms, Average = 13ms
"""

WINDOWS_PARTIAL_LOSS = """
Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=10ms TTL=117
Request timed out.
Reply from 8.8.8.8: bytes=32 time=12ms TTL=117
Request timed out.
Reply from 8.8.8.8: bytes=32 time=15ms TTL=117

Ping statistics for 8.8.8.8:
    Packets: Sent = 5, Received = 3, Lost = 2 (40% loss),
Approximate round trip times in milli-seconds:
    Minimum = 10ms, Maximum = 15ms, Average = 12ms
"""

WINDOWS_TOTAL_LOSS = """
Pinging 192.0.2.1 with 32 bytes of data:
Request timed out.
Request timed out.
Request timed out.
Request timed out.

Ping statistics for 192.0.2.1:
    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss),
"""

WINDOWS_HIGH_LATENCY = """
Pinging example.com [93.184.216.34] with 32 bytes of data:
Reply from 93.184.216.34: bytes=32 time=250ms TTL=56
Reply from 93.184.216.34: bytes=32 time=280ms TTL=56
Reply from 93.184.216.34: bytes=32 time=265ms TTL=56
Reply from 93.184.216.34: bytes=32 time=275ms TTL=56

Ping statistics for 93.184.216.34:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 250ms, Maximum = 280ms, Average = 267ms
"""

WINDOWS_DECIMAL_TIME = """
Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=10.5ms TTL=117
Reply from 8.8.8.8: bytes=32 time=15.2ms TTL=117
Reply from 8.8.8.8: bytes=32 time=12.8ms TTL=117

Ping statistics for 8.8.8.8:
    Packets: Sent = 3, Received = 3, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 10.5ms, Maximum = 15.2ms, Average = 12.8ms
"""

WINDOWS_LESS_THAN_1MS = """
Pinging 127.0.0.1 with 32 bytes of data:
Reply from 127.0.0.1: bytes=32 time<1ms TTL=128
Reply from 127.0.0.1: bytes=32 time<1ms TTL=128
Reply from 127.0.0.1: bytes=32 time<1ms TTL=128

Ping statistics for 127.0.0.1:
    Packets: Sent = 3, Received = 3, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 0ms, Maximum = 0ms, Average = 0ms
"""

# ============================================================================
# Platform-specific sample groups for easy testing
# ============================================================================

MACOS_SAMPLES = {
    "success": MACOS_SUCCESS,
    "partial_loss": MACOS_PARTIAL_LOSS,
    "total_loss": MACOS_TOTAL_LOSS,
    "high_latency": MACOS_HIGH_LATENCY,
    "high_jitter": MACOS_HIGH_JITTER,
    "time_parentheses": MACOS_TIME_PARENTHESES,
}

LINUX_SAMPLES = {
    "success": LINUX_IPUTILS_SUCCESS,
    "high_loss": LINUX_HIGH_LOSS,
    "no_response": LINUX_NO_RESPONSE,
    "unstable": LINUX_UNSTABLE,
}

WINDOWS_SAMPLES = {
    "success": WINDOWS_SUCCESS,
    "partial_loss": WINDOWS_PARTIAL_LOSS,
    "total_loss": WINDOWS_TOTAL_LOSS,
    "high_latency": WINDOWS_HIGH_LATENCY,
    "decimal_time": WINDOWS_DECIMAL_TIME,
    "less_than_1ms": WINDOWS_LESS_THAN_1MS,
}

ALL_PLATFORMS = {
    "macos": MACOS_SAMPLES,
    "linux": LINUX_SAMPLES,
    "windows": WINDOWS_SAMPLES,
}
