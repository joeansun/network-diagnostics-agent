from datetime import datetime, timezone

import netdiag.data.ping as ping
from netdiag.os.base import OSAdapter


def diagnose_from_signals(signal: ping.PingSignals) -> ping.DiagnosisCause:
    if signal.no_reply:
        return ping.DiagnosisCause.NO_CONNECTIVITY
    elif signal.high_loss:
        return ping.DiagnosisCause.HIGH_LOSS
    elif signal.unstable_jitter:
        return ping.DiagnosisCause.UNSTABLE_JITTER
    elif signal.high_latency:
        return ping.DiagnosisCause.HIGH_LATENCY
    else:
        return ping.DiagnosisCause.OK


def build_ping_metrics(ping_info: ping.PingParseResult) -> ping.PingMetrics:
    return ping.PingMetrics(
        sent=ping_info.sent,
        received=ping_info.received,
        loss_pct=ping_info.loss_pct,
        rtt_min_ms=ping_info.rtt_min_ms,
        rtt_avg_ms=ping_info.rtt_avg_ms,
        rtt_max_ms=ping_info.rtt_max_ms,
        rtt_stddev_ms=ping_info.rtt_stddev_ms,
        jitter=ping_info.jitter,
        jitter_ratio=ping_info.jitter_ratio,
    )


def build_ping_signals(ping_metrics: ping.PingMetrics) -> ping.PingSignals:
    return ping.PingSignals(
        no_reply=ping_metrics.received == 0,
        any_loss=ping_metrics.loss_pct > 0.0,
        high_loss=ping_metrics.loss_pct >= ping.HIGH_PACKET_LOSS_THRESHOLD_PCT,
        high_latency=ping_metrics.rtt_avg_ms >= ping.HIGH_LATENCY_THRESHOLD_MS,
        # unstable jitter must satisfy both conditions so fewer false alert
        unstable_jitter=ping_metrics.jitter_ratio >= ping.UNSTABLE_JITTER
        and ping_metrics.jitter >= ping.UNSTABLE_JITTER_ABS_MS,
        unstable=(
            ping_metrics.rtt_stddev_ms >= ping.UNSTABLE_DEVIATION * ping_metrics.rtt_avg_ms
            or (ping_metrics.rtt_max_ms - ping_metrics.rtt_min_ms) >= ping.UNSTABLE_RTT_SPREAD_MS
        ),
    )


def summarise_causes(cause: ping.DiagnosisCause) -> str:
    return ping.CAUSE_SUMMARY.get(cause, "Unknown or unclassified condition.")


# confidence is a value between [0.0, 1.0], 1.0 represents very cause
def compute_confidence(ping_metrics: ping.PingMetrics, cause: ping.DiagnosisCause) -> float:
    if cause == ping.DiagnosisCause.NO_CONNECTIVITY:
        cfd_value = 1.0
    elif cause == ping.DiagnosisCause.HIGH_LOSS:
        # Precondition: loss_pct >= 5.0
        if ping_metrics.loss_pct >= ping.LOSS_T1:
            cfd_value = 0.95
        elif ping_metrics.loss_pct >= ping.LOSS_T2:
            cfd_value = 0.85
        else:
            cfd_value = 0.70
    elif cause == ping.DiagnosisCause.UNSTABLE_JITTER:
        # Precondition: jitter_ratio >= 0.25 and jitter > 5 ms
        if ping_metrics.jitter_ratio >= ping.JIT_R1 and ping_metrics.jitter >= ping.JIT_A1:
            cfd_value = 0.95
        elif ping_metrics.jitter_ratio >= ping.JIT_R2 and ping_metrics.jitter >= ping.JIT_A2:
            cfd_value = 0.85
        else:
            cfd_value = 0.70
    elif cause == ping.DiagnosisCause.HIGH_LATENCY:
        # Precondition: rtt_avg_ms >= 150 ms
        if ping_metrics.rtt_avg_ms >= ping.LAT_T1:
            cfd_value = 0.95
        elif ping_metrics.rtt_avg_ms >= ping.LAT_T2:
            cfd_value = 0.85
        else:
            cfd_value = 0.70
    elif cause == ping.DiagnosisCause.OK:
        cfd_value = 1.0
    else:
        cfd_value = 0.5

    if ping_metrics.sent < 20 and cause not in (
        ping.DiagnosisCause.OK,
        ping.DiagnosisCause.NO_CONNECTIVITY,
    ):
        cfd_value = max(0.30, cfd_value - 0.20)

    # defensive for future usage
    return min(1.0, max(0.0, cfd_value))


def summarise_evidence(
    ping_metrics: ping.PingMetrics, cause: ping.DiagnosisCause
) -> dict[str, float]:
    evidence = {}
    for field in ping.CAUSE_EVIDENCE_FIELDS[cause]:
        evidence[field] = getattr(ping_metrics, field)

    return evidence


def build_ping_diagnosis(
    ping_metrics: ping.PingMetrics, ping_signals: ping.PingSignals
) -> ping.PingDiagnosis:
    cause = diagnose_from_signals(ping_signals)
    return ping.PingDiagnosis(
        cause=cause,
        summary=summarise_causes(cause),
        confidence=compute_confidence(ping_metrics, cause),
        evidence=summarise_evidence(ping_metrics, cause),
    )


def build_record(
    *,
    now: datetime,
    session_id: str,
    ping_info: ping.PingParseResult,
    ping_metrics: ping.PingMetrics,
    ping_signals: ping.PingSignals,
    ping_diagnosis: ping.PingDiagnosis,
) -> ping.PingRecord:
    return ping.PingRecord(
        session_id=session_id,
        timestamp=now,  # now.strftime("%Y-%m-%dT%H:%M:%SZ")
        target=ping_info.address,
        metrics=ping_metrics,
        signals=ping_signals,
        diagnosis=ping_diagnosis,
    )


def ping_analysis(os_adapter: OSAdapter, raw_input: str, session_id: str) -> ping.PingRecord:
    ping_info = os_adapter.parse_ping(raw_input)
    ping_metrics = build_ping_metrics(ping_info)
    ping_signals = build_ping_signals(ping_metrics)
    ping_diagnosis = build_ping_diagnosis(ping_metrics, ping_signals)

    now = datetime.now(timezone.utc)

    return build_record(
        now=now,
        session_id=session_id,
        ping_info=ping_info,
        ping_metrics=ping_metrics,
        ping_signals=ping_signals,
        ping_diagnosis=ping_diagnosis,
    )
