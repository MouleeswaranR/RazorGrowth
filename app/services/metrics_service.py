import time
from typing import Dict
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricCounter:
    """Simple counter metric."""
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    def inc(self, amount: int = 1) -> None:
        """Increments counter."""
        self.value += amount


@dataclass
class MetricGauge:
    """Simple gauge metric."""
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float) -> None:
        """Sets gauge value."""
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increments gauge."""
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrements gauge."""
        self.value -= amount


@dataclass
class MetricHistogram:
    """Simple histogram metric for tracking distributions."""
    count: int = 0
    sum: float = 0.0
    buckets: Dict[float, int] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    def observe(self, value: float) -> None:
        """Records a value."""
        self.count += 1
        self.sum += value


class MetricsService:
    """Prometheus-compatible metrics collection service for observability."""

    def __init__(self) -> None:
        """Initializes metrics registry and seeds baseline metrics."""
        self._counters: Dict[str, MetricCounter] = {}
        self._gauges: Dict[str, MetricGauge] = {}
        self._histograms: Dict[str, MetricHistogram] = {}

        # Seed baseline metrics so Prometheus endpoints are immediately populated
        self.counter("http_requests_total", {"endpoint": "/api/v1/growth/scan", "status": "200"}).inc(0)
        self.counter("agent_executions_total", {"agent": "GrowthManagerAgent", "status": "success"}).inc(0)
        self.counter("razorpay_api_calls_total", {"operation": "create_order", "status": "success"}).inc(0)
        self.counter("llm_tokens_used_total", {"provider": "nvidia_nim"}).inc(0)
        self.gauge("active_sessions").set(1.0)
        self.gauge("razorgrowth_system_status", {"mode": "test_sandbox"}).set(1.0)
        self.histogram("agent_execution_duration_ms", {"agent": "GrowthManagerAgent"}).observe(0.0)


    def counter(self, name: str, labels: Dict[str, str] | None = None) -> MetricCounter:
        """Gets or creates a counter metric."""
        key = self._make_key(name, labels)
        if key not in self._counters:
            self._counters[key] = MetricCounter(labels=labels or {})
        return self._counters[key]

    def gauge(self, name: str, labels: Dict[str, str] | None = None) -> MetricGauge:
        """Gets or creates a gauge metric."""
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = MetricGauge(labels=labels or {})
        return self._gauges[key]

    def histogram(self, name: str, labels: Dict[str, str] | None = None) -> MetricHistogram:
        """Gets or creates a histogram metric."""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = MetricHistogram(labels=labels or {})
        return self._histograms[key]

    def _make_key(self, name: str, labels: Dict[str, str] | None) -> str:
        """Creates unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics(self) -> Dict[str, Dict]:
        """Returns all metrics in Prometheus-compatible format."""
        metrics = {
            "counters": {
                name: {"value": counter.value, "labels": counter.labels}
                for name, counter in self._counters.items()
            },
            "gauges": {
                name: {"value": gauge.value, "labels": gauge.labels}
                for name, gauge in self._gauges.items()
            },
            "histograms": {
                name: {
                    "count": hist.count,
                    "sum": hist.sum,
                    "avg": hist.sum / hist.count if hist.count > 0 else 0.0,
                    "labels": hist.labels,
                }
                for name, hist in self._histograms.items()
            },
        }
        return metrics

    def export_prometheus_format(self) -> str:
        """Exports metrics in Prometheus text format."""
        lines = []

        for name, counter in self._counters.items():
            lines.append(f"# TYPE {name.split('{')[0]} counter")
            lines.append(f"{name} {counter.value}")

        for name, gauge in self._gauges.items():
            lines.append(f"# TYPE {name.split('{')[0]} gauge")
            lines.append(f"{name} {gauge.value}")

        for name, hist in self._histograms.items():
            base_name = name.split('{')[0]
            lines.append(f"# TYPE {base_name} histogram")
            lines.append(f"{base_name}_count {hist.count}")
            lines.append(f"{base_name}_sum {hist.sum}")

        return "\n".join(lines)

    # Convenience methods for common metrics
    def track_api_request(self, endpoint: str, method: str, status_code: int) -> None:
        """Tracks API request metrics."""
        self.counter("http_requests_total", {
            "endpoint": endpoint,
            "method": method,
            "status": str(status_code),
        }).inc()

    def track_agent_execution(self, agent_name: str, duration_ms: float, status: str) -> None:
        """Tracks agent execution metrics."""
        self.histogram("agent_execution_duration_ms", {"agent": agent_name}).observe(duration_ms)
        self.counter("agent_executions_total", {
            "agent": agent_name,
            "status": status,
        }).inc()

    def track_razorpay_api_call(self, operation: str, duration_ms: float, success: bool) -> None:
        """Tracks Razorpay API call metrics."""
        self.histogram("razorpay_api_duration_ms", {"operation": operation}).observe(duration_ms)
        self.counter("razorpay_api_calls_total", {
            "operation": operation,
            "status": "success" if success else "failure",
        }).inc()

    def track_llm_request(self, provider: str, duration_ms: float, tokens_used: int) -> None:
        """Tracks LLM request metrics."""
        self.histogram("llm_request_duration_ms", {"provider": provider}).observe(duration_ms)
        self.counter("llm_tokens_used_total", {"provider": provider}).inc(tokens_used)

    def set_active_sessions(self, count: int) -> None:
        """Sets current active sessions gauge."""
        self.gauge("active_sessions").set(float(count))


# Global singleton instance
metrics_service = MetricsService()
