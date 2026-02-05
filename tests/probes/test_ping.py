"""Tests for ping probe execution

Unit tests for run_ping use mocks (fast).
Integration tests marked with @pytest.mark.integration run real commands (slow).
"""

import subprocess
from unittest.mock import Mock

import pytest

from netdiag.data.ping import DiagnosisCause
from netdiag.probes.ping import run_ping
from tests.fixtures.ping_samples import (
    LINUX_HIGH_LOSS,
    LINUX_NO_RESPONSE,
    MACOS_HIGH_JITTER,
    MACOS_HIGH_LATENCY,
    MACOS_PARTIAL_LOSS,
    MACOS_SUCCESS,
    MACOS_TOTAL_LOSS,
)


# ============================================================================
# Unit Tests - Using mocked OS adapter
# ============================================================================


class TestRunPingUnit:
    """Unit tests for run_ping using mocked dependencies"""

    def test_successful_ping(self):
        """Test processing successful ping output"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_SUCCESS, stderr=""
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
        assert record.metrics.sent == 5
        assert record.metrics.received == 5
        assert record.diagnosis.cause == DiagnosisCause.OK
        mock_adapter.execute_ping.assert_called_once()

    def test_ping_with_packet_loss(self):
        """Test processing ping with packet loss"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_PARTIAL_LOSS, stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[10.5, 12.3, 15.7],
            sent=5,
            received=3,
            loss_pct=40.0,
            rtt_min_ms=10.5,
            rtt_avg_ms=12.8,
            rtt_max_ms=15.7,
            rtt_stddev_ms=2.1,
            jitter=2.6,
            jitter_ratio=0.20,
        )

        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=5,
            timeout_ms=1000,
            run_id="test-123",
        )

        assert record.metrics.loss_pct == 40.0
        assert record.signals.high_loss

    def test_ping_total_loss(self):
        """Test processing ping with total loss"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_TOTAL_LOSS, stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="192.0.2.1",
            times_ms=[],
            sent=5,
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
        assert record.diagnosis.cause == DiagnosisCause.NO_CONNECTIVITY

    def test_ping_high_latency(self):
        """Test processing ping with high latency"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_HIGH_LATENCY, stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="93.184.216.34",
            times_ms=[250.1, 280.4, 265.7, 275.2, 290.5],
            sent=5,
            received=5,
            loss_pct=0.0,
            rtt_min_ms=250.1,
            rtt_avg_ms=272.4,
            rtt_max_ms=290.5,
            rtt_stddev_ms=14.5,
            jitter=15.0,
            jitter_ratio=0.05,
        )

        record = run_ping(
            host="93.184.216.34",
            os_adapter=mock_adapter,
            count=5,
            timeout_ms=2000,
            run_id="test-123",
        )

        assert record.metrics.rtt_avg_ms > 250
        assert record.signals.high_latency
        assert record.diagnosis.cause == DiagnosisCause.HIGH_LATENCY

    def test_ping_unstable_jitter(self):
        """Test processing ping with high jitter"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_HIGH_JITTER, stderr=""
        )
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

    def test_gateway_resolution(self):
        """Test special 'gateway' host resolution"""
        mock_adapter = Mock()
        mock_adapter.get_gateway_ip.return_value = "192.168.1.1"
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_SUCCESS, stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="192.168.1.1",
            times_ms=[1.0, 1.2, 1.1],
            sent=3,
            received=3,
            loss_pct=0.0,
            rtt_min_ms=1.0,
            rtt_avg_ms=1.1,
            rtt_max_ms=1.2,
            rtt_stddev_ms=0.08,
            jitter=0.1,
            jitter_ratio=0.09,
        )

        record = run_ping(
            host="gateway",
            os_adapter=mock_adapter,
            count=3,
            timeout_ms=500,
            run_id="test-123",
        )

        mock_adapter.get_gateway_ip.assert_called_once()
        assert record.target == "192.168.1.1"

    def test_run_id_propagation(self):
        """Test run_id is properly set in record"""
        mock_adapter = Mock()
        mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
            args=["ping"], returncode=0, stdout=MACOS_SUCCESS, stderr=""
        )
        mock_adapter.parse_ping.return_value = Mock(
            address="8.8.8.8",
            times_ms=[10.0],
            sent=1,
            received=1,
            loss_pct=0.0,
            rtt_min_ms=10.0,
            rtt_avg_ms=10.0,
            rtt_max_ms=10.0,
            rtt_stddev_ms=0.0,
            jitter=0.0,
            jitter_ratio=0.0,
        )

        run_id = "custom-run-id-456"
        record = run_ping(
            host="8.8.8.8",
            os_adapter=mock_adapter,
            count=1,
            timeout_ms=1000,
            run_id=run_id,
        )

        assert record.run_id == run_id


# ============================================================================
# Integration Tests - Real command execution (optional, marked slow)
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestRunPingIntegration:
    """Integration tests using real OS adapter and commands

    These tests execute real ping commands and are slower.
    Run with: pytest -m integration
    Skip with: pytest -m "not integration"
    """

    @pytest.fixture
    def real_adapter(self):
        """Get the real OS adapter for current platform"""
        from netdiag.os import get_os_adapter

        return get_os_adapter()

    def test_ping_localhost(self, real_adapter):
        """Test pinging localhost (should always work)"""
        record = run_ping(
            host="127.0.0.1",
            os_adapter=real_adapter,
            count=3,
            timeout_ms=1000,
            run_id="integration-test",
        )

        assert record.target == "127.0.0.1"
        assert record.metrics.sent == 3
        # Allow some packet loss on CI/CD systems
        assert record.metrics.received >= 2
        # Skip RTT checks if metrics are zero (Windows localhost edge case)
        if record.metrics.rtt_avg_ms > 0:
            assert record.metrics.rtt_avg_ms < 100

    def test_ping_unreachable_host(self, real_adapter):
        """Test pinging unreachable host"""
        # Use TEST-NET-1 reserved IP (should be unreachable)
        record = run_ping(
            host="192.0.2.1",
            os_adapter=real_adapter,
            count=2,
            timeout_ms=500,
            run_id="integration-test",
        )

        assert record.metrics.sent == 2
        assert record.metrics.received == 0
        assert record.metrics.loss_pct == 100.0
        assert record.diagnosis.cause == DiagnosisCause.NO_CONNECTIVITY

    @pytest.mark.network
    def test_ping_real_dns_server(self, real_adapter):
        """Test pinging Google DNS (requires internet)

        This test requires network access. Skip in offline environments.
        """
        record = run_ping(
            host="8.8.8.8",
            os_adapter=real_adapter,
            count=3,
            timeout_ms=2000,
            run_id="integration-test",
        )

        assert record.metrics.sent == 3
        # Should succeed if network is available
        assert record.metrics.received > 0
        # Internet latency varies but should be reasonable
        if record.metrics.received > 0:
            assert record.metrics.rtt_avg_ms < 1000
