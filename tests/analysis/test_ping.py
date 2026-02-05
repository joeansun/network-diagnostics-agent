"""Tests for ping analysis logic

Tests pure analysis functions with real data. No mocking needed
since these are deterministic transformations.
"""

import pytest

from netdiag.analysis.ping import (
    build_ping_diagnosis,
    build_ping_metrics,
    build_ping_signals,
    compute_confidence,
    diagnose_from_signals,
    summarise_causes,
    summarise_evidence,
)
from netdiag.data.ping import DiagnosisCause, PingMetrics, PingParseResult, PingSignals


class TestBuildPingMetrics:
    """Test metrics building from parse results"""

    def test_converts_parse_result_to_metrics(self):
        parse_result = PingParseResult(
            address="8.8.8.8",
            times_ms=[10.0, 15.0, 20.0],
            sent=3,
            received=3,
            loss_pct=0.0,
            rtt_min_ms=10.0,
            rtt_avg_ms=15.0,
            rtt_max_ms=20.0,
            rtt_stddev_ms=4.08,
            jitter=5.0,
            jitter_ratio=0.33,
        )

        metrics = build_ping_metrics(parse_result)

        assert metrics.sent == 3
        assert metrics.received == 3
        assert metrics.loss_pct == 0.0
        assert metrics.rtt_min_ms == 10.0


class TestBuildPingSignals:
    """Test signal detection from metrics"""

    def test_healthy_connection(self, healthy_metrics):
        signals = build_ping_signals(healthy_metrics)
        assert not any([
            signals.no_reply,
            signals.any_loss,
            signals.high_loss,
            signals.high_latency,
            signals.unstable_jitter,
        ])

    def test_no_connectivity(self, no_connectivity_metrics):
        signals = build_ping_signals(no_connectivity_metrics)
        assert all([signals.no_reply, signals.any_loss, signals.high_loss])

    def test_high_loss(self, high_loss_metrics):
        signals = build_ping_signals(high_loss_metrics)
        assert signals.high_loss and signals.any_loss
        assert not signals.no_reply

    def test_high_latency(self, high_latency_metrics):
        signals = build_ping_signals(high_latency_metrics)
        assert signals.high_latency
        assert not signals.any_loss

    def test_high_jitter(self, high_jitter_metrics):
        signals = build_ping_signals(high_jitter_metrics)
        assert signals.unstable_jitter and signals.unstable

    @pytest.mark.parametrize("loss_pct,expected", [
        (5.0, True),   # At threshold
        (4.9, False),  # Below threshold
        (10.0, True),  # Above threshold
    ])
    def test_loss_threshold(self, loss_pct, expected):
        metrics = PingMetrics(
            sent=100, received=int(100 - loss_pct), loss_pct=loss_pct,
            rtt_min_ms=10.0, rtt_avg_ms=15.0, rtt_max_ms=20.0,
            rtt_stddev_ms=3.0, jitter=2.0, jitter_ratio=0.13,
        )
        assert build_ping_signals(metrics).high_loss == expected


class TestDiagnoseFromSignals:
    """Test diagnosis inference from signals"""

    @pytest.mark.parametrize("signals,expected_cause", [
        # Test priority order
        (
            PingSignals(no_reply=True, any_loss=True, high_loss=True,
                       high_latency=False, unstable_jitter=False, unstable=False),
            DiagnosisCause.NO_CONNECTIVITY
        ),
        (
            PingSignals(no_reply=False, any_loss=True, high_loss=True,
                       high_latency=False, unstable_jitter=False, unstable=False),
            DiagnosisCause.HIGH_LOSS
        ),
        (
            PingSignals(no_reply=False, any_loss=False, high_loss=False,
                       high_latency=False, unstable_jitter=True, unstable=True),
            DiagnosisCause.UNSTABLE_JITTER
        ),
        (
            PingSignals(no_reply=False, any_loss=False, high_loss=False,
                       high_latency=True, unstable_jitter=False, unstable=False),
            DiagnosisCause.HIGH_LATENCY
        ),
        (
            PingSignals(no_reply=False, any_loss=False, high_loss=False,
                       high_latency=False, unstable_jitter=False, unstable=False),
            DiagnosisCause.OK
        ),
    ])
    def test_diagnosis_priority(self, signals, expected_cause):
        assert diagnose_from_signals(signals) == expected_cause


class TestComputeConfidence:
    """Test confidence scoring"""

    def test_perfect_confidence_cases(self, healthy_metrics, no_connectivity_metrics):
        assert compute_confidence(healthy_metrics, DiagnosisCause.OK) == 1.0
        assert compute_confidence(no_connectivity_metrics, DiagnosisCause.NO_CONNECTIVITY) == 1.0

    @pytest.mark.parametrize("loss_pct,expected_confidence", [
        (20.0, 0.95),  # Very high loss
        (10.0, 0.85),  # Moderate loss
        (6.0, 0.70),   # Low loss
    ])
    def test_high_loss_tiers(self, loss_pct, expected_confidence):
        metrics = PingMetrics(
            sent=100, received=int(100 - loss_pct), loss_pct=loss_pct,
            rtt_min_ms=10.0, rtt_avg_ms=15.0, rtt_max_ms=20.0,
            rtt_stddev_ms=3.0, jitter=2.0, jitter_ratio=0.13,
        )
        assert compute_confidence(metrics, DiagnosisCause.HIGH_LOSS) == expected_confidence

    def test_small_sample_penalty(self):
        """Small samples reduce confidence"""
        small_sample = PingMetrics(
            sent=5, received=3, loss_pct=40.0,
            rtt_min_ms=10.0, rtt_avg_ms=15.0, rtt_max_ms=20.0,
            rtt_stddev_ms=3.0, jitter=2.0, jitter_ratio=0.13,
        )
        confidence = compute_confidence(small_sample, DiagnosisCause.HIGH_LOSS)
        assert confidence <= 0.75

    def test_confidence_bounds(self, healthy_metrics):
        """Confidence always between 0 and 1"""
        for cause in DiagnosisCause:
            confidence = compute_confidence(healthy_metrics, cause)
            assert 0.0 <= confidence <= 1.0


class TestSummariseCauses:
    """Test cause summarization"""

    def test_all_causes_have_summaries(self):
        for cause in DiagnosisCause:
            summary = summarise_causes(cause)
            assert isinstance(summary, str) and len(summary) > 0


class TestSummariseEvidence:
    """Test evidence collection"""

    @pytest.mark.parametrize("cause,expected_fields", [
        (DiagnosisCause.OK, ["loss_pct", "rtt_avg_ms"]),
        (DiagnosisCause.HIGH_LOSS, ["loss_pct", "sent", "received"]),
        (DiagnosisCause.NO_CONNECTIVITY, ["sent", "received", "loss_pct"]),
    ])
    def test_evidence_fields(self, healthy_metrics, cause, expected_fields):
        evidence = summarise_evidence(healthy_metrics, cause)
        for field in expected_fields:
            assert field in evidence


class TestBuildPingDiagnosis:
    """Test complete diagnosis building"""

    @pytest.mark.parametrize("metrics_fixture,expected_cause", [
        ("healthy_metrics", DiagnosisCause.OK),
        ("no_connectivity_metrics", DiagnosisCause.NO_CONNECTIVITY),
        ("high_loss_metrics", DiagnosisCause.HIGH_LOSS),
        ("high_latency_metrics", DiagnosisCause.HIGH_LATENCY),
        ("high_jitter_metrics", DiagnosisCause.UNSTABLE_JITTER),
    ])
    def test_end_to_end_diagnosis(self, metrics_fixture, expected_cause, request):
        """Test full diagnosis pipeline for different scenarios"""
        metrics = request.getfixturevalue(metrics_fixture)
        signals = build_ping_signals(metrics)
        diagnosis = build_ping_diagnosis(metrics, signals)

        assert diagnosis.cause == expected_cause
        assert 0.0 < diagnosis.confidence <= 1.0
        assert isinstance(diagnosis.summary, str)
        assert isinstance(diagnosis.evidence, dict)
