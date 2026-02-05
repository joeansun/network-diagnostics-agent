"""Shared fixtures for all tests

This file is automatically discovered by pytest and makes fixtures
available to all test files without explicit imports.
"""

import pytest

from netdiag.data.ping import PingMetrics

# ============================================================================
# Shared Metric Fixtures
# ============================================================================


@pytest.fixture
def healthy_metrics():
    """Metrics for a healthy connection"""
    return PingMetrics(
        sent=10,
        received=10,
        loss_pct=0.0,
        rtt_min_ms=10.0,
        rtt_avg_ms=15.0,
        rtt_max_ms=20.0,
        rtt_stddev_ms=3.0,
        jitter=2.0,
        jitter_ratio=0.13,
    )


@pytest.fixture
def high_loss_metrics():
    """Metrics with significant packet loss"""
    return PingMetrics(
        sent=10,
        received=5,
        loss_pct=50.0,
        rtt_min_ms=10.0,
        rtt_avg_ms=15.0,
        rtt_max_ms=20.0,
        rtt_stddev_ms=3.0,
        jitter=2.0,
        jitter_ratio=0.13,
    )


@pytest.fixture
def high_latency_metrics():
    """Metrics with high latency"""
    return PingMetrics(
        sent=10,
        received=10,
        loss_pct=0.0,
        rtt_min_ms=250.0,
        rtt_avg_ms=280.0,
        rtt_max_ms=310.0,
        rtt_stddev_ms=20.0,
        jitter=15.0,
        jitter_ratio=0.05,
    )


@pytest.fixture
def high_jitter_metrics():
    """Metrics with unstable connection (high jitter)"""
    return PingMetrics(
        sent=10,
        received=10,
        loss_pct=0.0,
        rtt_min_ms=5.0,
        rtt_avg_ms=50.0,
        rtt_max_ms=150.0,
        rtt_stddev_ms=45.0,
        jitter=40.0,
        jitter_ratio=0.8,
    )


@pytest.fixture
def no_connectivity_metrics():
    """Metrics for complete connection failure"""
    return PingMetrics(
        sent=10,
        received=0,
        loss_pct=100.0,
        rtt_min_ms=0.0,
        rtt_avg_ms=0.0,
        rtt_max_ms=0.0,
        rtt_stddev_ms=0.0,
        jitter=0.0,
        jitter_ratio=0.0,
    )
