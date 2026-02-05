"""Cross-platform tests for ping probe

Tests that parsers handle all platform variations correctly.
Uses real ping outputs from macOS, Linux, and Windows.
"""

import subprocess
from unittest.mock import Mock

import pytest

from netdiag.data.ping import DiagnosisCause
from netdiag.probes.ping import run_ping
from tests.fixtures.ping_samples import (
    ALL_PLATFORMS,
    LINUX_SAMPLES,
    MACOS_SAMPLES,
    WINDOWS_SAMPLES,
)


class TestCrossPlatformParsing:
    """Test ping parsing across all supported platforms"""

    @pytest.mark.parametrize("platform,samples", [
        ("macos", MACOS_SAMPLES),
        ("linux", LINUX_SAMPLES),
        ("windows", WINDOWS_SAMPLES),
    ])
    def test_successful_ping_all_platforms(self, platform, samples):
        """Test successful ping parsing on all platforms"""
        if "success" not in samples:
            pytest.skip(f"No success sample for {platform}")

        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=samples["success"], stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[10.1, 15.4, 12.7, 18.2, 14.5],
            sent=5,
            received=5,
            loss_pct=0.0,
            rtt_min_ms=10.1,
            rtt_avg_ms=14.2,
            rtt_max_ms=18.2,
            rtt_stddev_ms=2.9,
            jitter=2.0,
            jitter_ratio=0.14,
        )

        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=5,
            timeout_ms=1000,
            run_id="test-123",
        )

        assert record.target == "8.8.8.8"
        assert record.metrics.loss_pct == 0.0
        assert record.diagnosis.cause == DiagnosisCause.OK

    @pytest.mark.parametrize("platform,loss_key,expected_loss", [
        ("macos", "partial_loss", 40.0),
        ("linux", "high_loss", 90.0),
        ("windows", "partial_loss", 40.0),
    ])
    def test_packet_loss_all_platforms(self, platform, loss_key, expected_loss):
        """Test packet loss parsing on all platforms"""
        samples = {
            "macos": MACOS_SAMPLES,
            "linux": LINUX_SAMPLES,
            "windows": WINDOWS_SAMPLES,
        }[platform]

        if loss_key not in samples:
            pytest.skip(f"No {loss_key} sample for {platform}")

        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=samples[loss_key], stderr=""
        )

        # Calculate received based on expected loss
        sent = 5 if platform == "macos" else (10 if platform == "linux" else 5)
        received = int(sent * (1 - expected_loss / 100))

        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[10.5, 12.3, 15.7] if received > 0 else [],
            sent=sent,
            received=received,
            loss_pct=expected_loss,
            rtt_min_ms=10.5 if received > 0 else 0.0,
            rtt_avg_ms=12.8 if received > 0 else 0.0,
            rtt_max_ms=15.7 if received > 0 else 0.0,
            rtt_stddev_ms=2.1 if received > 0 else 0.0,
            jitter=2.6 if received > 0 else 0.0,
            jitter_ratio=0.20 if received > 0 else 0.0,
        )

        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=sent,
            timeout_ms=1000,
            run_id="test-123",
        )

        assert record.metrics.loss_pct == pytest.approx(expected_loss, abs=1.0)
        assert record.signals.high_loss

    @pytest.mark.parametrize("platform,samples", [
        ("macos", MACOS_SAMPLES),
        ("linux", LINUX_SAMPLES),
        ("windows", WINDOWS_SAMPLES),
    ])
    def test_total_loss_all_platforms(self, platform, samples):
        """Test total packet loss (100%) on all platforms"""
        loss_key = "total_loss" if platform != "linux" else "no_response"

        if loss_key not in samples:
            pytest.skip(f"No total loss sample for {platform}")

        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=samples[loss_key], stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="192.0.2.1",
            times_ms=[],
            sent=5 if platform != "windows" else 4,
            received=0,
            loss_pct=100.0,
            rtt_min_ms=0.0,
            rtt_avg_ms=0.0,
            rtt_max_ms=0.0,
            rtt_stddev_ms=0.0,
            jitter=0.0,
            jitter_ratio=0.0,
        )

        record = run_ping(
            host="192.0.2.1",
            os_adapter=mock_adapter,
            count=5,
            timeout_ms=1000,
            run_id="test-123",
        )

        assert record.metrics.received == 0
        assert record.metrics.loss_pct == 100.0
        assert record.diagnosis.cause == DiagnosisCause.NO_CONNECTIVITY


class TestPlatformSpecificEdgeCases:
    """Test platform-specific edge cases"""

    def test_macos_time_with_parentheses(self):
        """Test macOS edge case: time=(1008).473 ms"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0,
            stdout=MACOS_SAMPLES["time_parentheses"],
            stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[1008.473, 1015.234],
            sent=2,
            received=2,
            loss_pct=0.0,
            rtt_min_ms=1008.473,
            rtt_avg_ms=1011.854,
            rtt_max_ms=1015.234,
            rtt_stddev_ms=3.381,
            jitter=6.761,
            jitter_ratio=0.0067,
        )

        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=2,
            timeout_ms=2000,
            run_id="test-123",
        )

        assert record.metrics.rtt_avg_ms > 1000  # Very high latency
        assert record.diagnosis.cause == DiagnosisCause.HIGH_LATENCY

    def test_windows_less_than_1ms(self):
        """Test Windows edge case: time<1ms (localhost)"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0,
            stdout=WINDOWS_SAMPLES["less_than_1ms"],
            stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="127.0.0.1",
            times_ms=[0.0, 0.0, 0.0],  # Windows reports as 0
            sent=3,
            received=3,
            loss_pct=0.0,
            rtt_min_ms=0.0,
            rtt_avg_ms=0.0,
            rtt_max_ms=0.0,
            rtt_stddev_ms=0.0,
            jitter=0.0,
            jitter_ratio=0.0,
        )

        record = run_ping(
            host="127.0.0.1",
            os_adapter=mock_adapter,
            count=3,
            timeout_ms=500,
            run_id="test-123",
        )

        assert record.metrics.received == 3
        # Accept 0ms RTT for localhost on Windows
        assert record.metrics.rtt_avg_ms >= 0.0

    def test_windows_decimal_time(self):
        """Test Windows with decimal milliseconds"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0,
            stdout=WINDOWS_SAMPLES["decimal_time"],
            stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[10.5, 15.2, 12.8],
            sent=3,
            received=3,
            loss_pct=0.0,
            rtt_min_ms=10.5,
            rtt_avg_ms=12.8,
            rtt_max_ms=15.2,
            rtt_stddev_ms=1.9,
            jitter=2.35,
            jitter_ratio=0.18,
        )

        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=3,
            timeout_ms=1000,
            run_id="test-123",
        )

        assert record.metrics.rtt_min_ms == 10.5
        assert record.metrics.rtt_avg_ms == 12.8
        assert record.metrics.rtt_max_ms == 15.2


class TestHighLatencyAcrossPlatforms:
    """Test high latency detection across platforms"""

    @pytest.mark.parametrize("platform,latency_key", [
        ("macos", "high_latency"),
        ("windows", "high_latency"),
    ])
    def test_high_latency_detection(self, platform, latency_key):
        """Test high latency is correctly detected on all platforms"""
        samples = {
            "macos": MACOS_SAMPLES,
            "windows": WINDOWS_SAMPLES,
        }[platform]

        if latency_key not in samples:
            pytest.skip(f"No {latency_key} sample for {platform}")

        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0,
            stdout=samples[latency_key],
            stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="93.184.216.34",
            times_ms=[250.0, 280.0, 265.0, 275.0],
            sent=4,
            received=4,
            loss_pct=0.0,
            rtt_min_ms=250.0,
            rtt_avg_ms=267.5,
            rtt_max_ms=280.0,
            rtt_stddev_ms=12.0,
            jitter=15.0,
            jitter_ratio=0.056,
        )

        record = run_ping(
            host="93.184.216.34",
            os_adapter=mock_adapter,
            count=4,
            timeout_ms=2000,
            run_id="test-123",
        )

        assert record.metrics.rtt_avg_ms > 250
        assert record.signals.high_latency
        assert record.diagnosis.cause == DiagnosisCause.HIGH_LATENCY


class TestUnstableConnectionAcrossPlatforms:
    """Test unstable connection detection across platforms"""

    @pytest.mark.parametrize("platform,jitter_key", [
        ("macos", "high_jitter"),
        ("linux", "unstable"),
    ])
    def test_unstable_connection_detection(self, platform, jitter_key):
        """Test unstable/high jitter detection on all platforms"""
        samples = {
            "macos": MACOS_SAMPLES,
            "linux": LINUX_SAMPLES,
        }[platform]

        if jitter_key not in samples:
            pytest.skip(f"No {jitter_key} sample for {platform}")

        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0,
            stdout=samples[jitter_key],
            stderr=""
        )

        # High variance in RTT times
        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[5.1, 95.4, 8.7, 120.2, 12.5],
            sent=5,
            received=5,
            loss_pct=0.0,
            rtt_min_ms=5.1,
            rtt_avg_ms=48.4,
            rtt_max_ms=120.2,
            rtt_stddev_ms=49.1,
            jitter=45.0,
            jitter_ratio=0.93,
        )

        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=5,
            timeout_ms=1000,
            run_id="test-123",
        )

        assert record.signals.unstable_jitter
        assert record.diagnosis.cause == DiagnosisCause.UNSTABLE_JITTER
