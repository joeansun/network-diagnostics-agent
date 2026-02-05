"""Tests for ping data structures and constants

These tests verify dataclasses, enums, and constants work correctly.
No mocking needed - pure data validation.
"""

import pytest

from netdiag.data.ping import (
    CAUSE_EVIDENCE_FIELDS,
    CAUSE_SUMMARY,
    DiagnosisCause,
    PingDiagnosis,
    PingMetrics,
    PingParseResult,
    PingRecord,
    PingSignals,
)


class TestDiagnosisCause:
    """Test diagnosis cause enum"""

    def test_all_causes_have_values(self):
        """Verify all enum members have string values"""
        for cause in DiagnosisCause:
            assert isinstance(cause.value, str)
            assert len(cause.value) > 0

    def test_all_causes_have_summaries(self):
        """Verify all causes have summary messages"""
        for cause in DiagnosisCause:
            assert cause in CAUSE_SUMMARY
            assert isinstance(CAUSE_SUMMARY[cause], str)
            assert len(CAUSE_SUMMARY[cause]) > 0

    def test_all_causes_have_evidence_fields(self):
        """Verify all causes have evidence field definitions"""
        for cause in DiagnosisCause:
            assert cause in CAUSE_EVIDENCE_FIELDS
            assert isinstance(CAUSE_EVIDENCE_FIELDS[cause], list)


class TestPingMetrics:
    """Test PingMetrics dataclass"""

    def test_create_valid_metrics(self):
        """Test creating valid ping metrics"""
        metrics = PingMetrics(
            sent=10,
            received=9,
            loss_pct=10.0,
            rtt_min_ms=5.0,
            rtt_avg_ms=15.0,
            rtt_max_ms=25.0,
            rtt_stddev_ms=5.0,
            jitter=3.5,
            jitter_ratio=0.23,
        )

        assert metrics.sent == 10
        assert metrics.received == 9
        assert metrics.loss_pct == 10.0
        assert metrics.rtt_min_ms == 5.0
        assert metrics.rtt_avg_ms == 15.0
        assert metrics.rtt_max_ms == 25.0

    def test_zero_loss_scenario(self):
        """Test metrics with no packet loss"""
        metrics = PingMetrics(
            sent=5,
            received=5,
            loss_pct=0.0,
            rtt_min_ms=10.0,
            rtt_avg_ms=15.0,
            rtt_max_ms=20.0,
            rtt_stddev_ms=3.0,
            jitter=2.0,
            jitter_ratio=0.13,
        )

        assert metrics.sent == metrics.received
        assert metrics.loss_pct == 0.0

    def test_total_loss_scenario(self):
        """Test metrics with complete packet loss"""
        metrics = PingMetrics(
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

        assert metrics.received == 0
        assert metrics.loss_pct == 100.0


class TestPingSignals:
    """Test PingSignals dataclass"""

    def test_all_ok_signals(self):
        """Test signals for healthy connection"""
        signals = PingSignals(
            no_reply=False,
            any_loss=False,
            high_loss=False,
            high_latency=False,
            unstable_jitter=False,
            unstable=False,
        )

        assert not signals.no_reply
        assert not signals.any_loss
        assert not signals.high_loss
        assert not signals.high_latency

    def test_no_connectivity_signals(self):
        """Test signals for no connectivity"""
        signals = PingSignals(
            no_reply=True,
            any_loss=True,
            high_loss=True,
            high_latency=False,
            unstable_jitter=False,
            unstable=False,
        )

        assert signals.no_reply
        assert signals.any_loss
        assert signals.high_loss

    def test_high_jitter_signals(self):
        """Test signals for unstable connection"""
        signals = PingSignals(
            no_reply=False,
            any_loss=False,
            high_loss=False,
            high_latency=False,
            unstable_jitter=True,
            unstable=True,
        )

        assert signals.unstable_jitter
        assert signals.unstable


class TestPingDiagnosis:
    """Test PingDiagnosis dataclass"""

    def test_create_ok_diagnosis(self):
        """Test creating OK diagnosis"""
        diagnosis = PingDiagnosis(
            cause=DiagnosisCause.OK,
            summary="Connection is healthy",
            confidence=1.0,
            evidence={"loss_pct": 0.0, "rtt_avg_ms": 15.0},
        )

        assert diagnosis.cause == DiagnosisCause.OK
        assert diagnosis.confidence == 1.0
        assert "loss_pct" in diagnosis.evidence

    def test_create_problem_diagnosis(self):
        """Test creating diagnosis with issues"""
        diagnosis = PingDiagnosis(
            cause=DiagnosisCause.HIGH_LOSS,
            summary="Packet loss is high",
            confidence=0.85,
            evidence={"loss_pct": 25.0, "sent": 10, "received": 7},
        )

        assert diagnosis.cause == DiagnosisCause.HIGH_LOSS
        assert 0.0 <= diagnosis.confidence <= 1.0
        assert diagnosis.confidence == 0.85

    def test_confidence_bounds(self):
        """Test confidence is always between 0 and 1"""
        for confidence in [0.0, 0.5, 0.95, 1.0]:
            diagnosis = PingDiagnosis(
                cause=DiagnosisCause.OK,
                summary="Test",
                confidence=confidence,
                evidence={},
            )
            assert 0.0 <= diagnosis.confidence <= 1.0


class TestPingParseResult:
    """Test PingParseResult dataclass"""

    def test_create_parse_result(self):
        """Test creating parse result with all fields"""
        result = PingParseResult(
            address="8.8.8.8",
            times_ms=[10.1, 15.2, 12.3],
            sent=3,
            received=3,
            loss_pct=0.0,
            rtt_min_ms=10.1,
            rtt_avg_ms=12.5,
            rtt_max_ms=15.2,
            rtt_stddev_ms=2.1,
            jitter=2.5,
            jitter_ratio=0.2,
        )

        assert result.address == "8.8.8.8"
        assert len(result.times_ms) == 3
        assert result.sent == result.received

    def test_parse_result_is_frozen(self):
        """Test that PingParseResult is immutable"""
        result = PingParseResult(
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

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            result.sent = 5


class TestPingRecord:
    """Test PingRecord dataclass"""

    def test_create_complete_record(self):
        """Test creating a complete ping record"""
        from datetime import datetime

        record = PingRecord(
            run_id="test-123",
            timestamp=datetime.now(),
            target="8.8.8.8",
            metrics=PingMetrics(
                sent=5,
                received=5,
                loss_pct=0.0,
                rtt_min_ms=10.0,
                rtt_avg_ms=15.0,
                rtt_max_ms=20.0,
                rtt_stddev_ms=3.0,
                jitter=2.0,
                jitter_ratio=0.13,
            ),
            signals=PingSignals(
                no_reply=False,
                any_loss=False,
                high_loss=False,
                high_latency=False,
                unstable_jitter=False,
                unstable=False,
            ),
            diagnosis=PingDiagnosis(
                cause=DiagnosisCause.OK,
                summary="Connection is healthy",
                confidence=1.0,
                evidence={},
            ),
        )

        assert record.run_id == "test-123"
        assert record.target == "8.8.8.8"
        assert isinstance(record.metrics, PingMetrics)
        assert isinstance(record.signals, PingSignals)
        assert isinstance(record.diagnosis, PingDiagnosis)
