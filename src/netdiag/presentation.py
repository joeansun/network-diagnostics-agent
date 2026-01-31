from netdiag.data.ping import *

def format_welcome_message():
    return "Welcome to the Network Diagnostics Agent!"

def format_ping_report(report: PingRecord) -> str:
    m = report.metrics
    d = report.diagnosis

    icon = "✓" if d.cause == DiagnosisCause.OK else "✗"


    return f"""
        {icon} {report.target} - {d.cause.value.upper()}
     {d.summary}
     Packets: {m.received}/{m.sent} ({m.loss_pct:.1f}% loss)
     Latency: {m.rtt_avg_ms:.1f}ms (min={m.rtt_min_ms:.1f}, max={m.rtt_max_ms:.1f})
     Jitter:  {m.jitter:.2f}ms
     Confidence: {d.confidence:.0%}
    """