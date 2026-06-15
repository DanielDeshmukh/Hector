"""Prometheus-compatible metrics for HECTOR."""
import time
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    """Thread-safe in-memory metrics collector."""

    def __init__(self):
        self._lock = Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.time()

    def inc(self, name: str, value: int = 1):
        """Increment a counter."""
        with self._lock:
            self._counters[name] += value

    def set(self, name: str, value: float):
        """Set a gauge value."""
        with self._lock:
            self._gauges[name] = value

    def observe(self, name: str, value: float):
        """Record a histogram observation."""
        with self._lock:
            self._histograms[name].append(value)

    def render(self) -> str:
        """Render all metrics in Prometheus text format."""
        lines = []
        uptime = time.time() - self._start_time

        # Uptime gauge
        lines.append("# HELP hector_uptime_seconds Time since process start")
        lines.append("# TYPE hector_uptime_seconds gauge")
        lines.append(f"hector_uptime_seconds {uptime:.1f}")

        # Counters
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            histograms = dict(self._histograms)

        for name, value in sorted(counters.items()):
            lines.append(f"# HELP hector_{name} Total count")
            lines.append(f"# TYPE hector_{name} counter")
            lines.append(f"hector_{name} {value}")

        for name, value in sorted(gauges.items()):
            lines.append(f"# HELP hector_{name} Current value")
            lines.append(f"# TYPE hector_{name} gauge")
            lines.append(f"hector_{name} {value}")

        for name, values in sorted(histograms.items()):
            if not values:
                continue
            values_sorted = sorted(values)
            count = len(values_sorted)
            total = sum(values_sorted)
            p50 = values_sorted[int(count * 0.5)] if count > 0 else 0
            p95 = values_sorted[int(count * 0.95)] if count > 0 else 0
            p99 = values_sorted[int(count * 0.99)] if count > 0 else 0
            lines.append(f"# HELP hector_{name}_seconds Request duration")
            lines.append(f"# TYPE hector_{name}_seconds histogram")
            lines.append(f"hector_{name}_seconds_count {count}")
            lines.append(f"hector_{name}_seconds_sum {total:.3f}")
            lines.append(f"hector_{name}_seconds{{quantile=\"0.5\"}} {p50:.3f}")
            lines.append(f"hector_{name}_seconds{{quantile=\"0.95\"}} {p95:.3f}")
            lines.append(f"hector_{name}_seconds{{quantile=\"0.99\"}} {p99:.3f}")

        return "\n".join(lines) + "\n"


# Global singleton
metrics = MetricsCollector()
