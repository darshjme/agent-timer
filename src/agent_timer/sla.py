"""SLA compliance tracker with percentile latency statistics."""

import math
from typing import Any


class SLAViolationError(Exception):
    """Raised when execution time exceeds the configured SLA."""

    def __init__(self, name: str, sla_ms: float, elapsed_ms: float) -> None:
        self.name = name
        self.sla_ms = sla_ms
        self.elapsed_ms = elapsed_ms
        over_ms = elapsed_ms - sla_ms
        super().__init__(
            f"SLA violation [{name}]: elapsed {elapsed_ms:.2f} ms exceeds "
            f"SLA of {sla_ms:.2f} ms (over by {over_ms:.2f} ms)"
        )


def _percentile(sorted_data: list[float], p: float) -> float:
    """
    Compute the p-th percentile of a sorted list using linear interpolation
    (same method as numpy.percentile with interpolation='linear').
    """
    n = len(sorted_data)
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_data[0]
    # Clamp p to [0, 100]
    p = max(0.0, min(100.0, p))
    index = (p / 100.0) * (n - 1)
    lo = int(math.floor(index))
    hi = int(math.ceil(index))
    frac = index - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


class SLATracker:
    """
    Tracks SLA compliance over many calls.

    Usage::

        tracker = SLATracker("llm-call", sla_ms=500)
        tracker.record(123.4)
        tracker.record(890.1)  # violation

        print(tracker.compliance_rate)  # 0.5
        print(tracker.p95_ms)           # 95th percentile
        print(tracker.stats())
    """

    def __init__(self, name: str, sla_ms: float) -> None:
        if sla_ms <= 0:
            raise ValueError(f"sla_ms must be positive, got {sla_ms}")
        self.name = name
        self.sla_ms = sla_ms
        self._durations: list[float] = []
        self._violations_count: int = 0

    # ------------------------------------------------------------------
    # Record
    # ------------------------------------------------------------------

    def record(self, duration_ms: float) -> None:
        """Record an execution time (milliseconds)."""
        self._durations.append(duration_ms)
        if duration_ms > self.sla_ms:
            self._violations_count += 1

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        """Total number of recorded calls."""
        return len(self._durations)

    @property
    def violations(self) -> int:
        """Number of calls that exceeded the SLA."""
        return self._violations_count

    @property
    def compliance_rate(self) -> float:
        """Fraction of calls within SLA (0.0–1.0). Returns 1.0 if no calls."""
        if not self._durations:
            return 1.0
        compliant = self.count - self._violations_count
        return compliant / self.count

    @property
    def p50_ms(self) -> float:
        """Median (50th percentile) latency in milliseconds."""
        return _percentile(sorted(self._durations), 50)

    @property
    def p95_ms(self) -> float:
        """95th percentile latency in milliseconds."""
        return _percentile(sorted(self._durations), 95)

    @property
    def p99_ms(self) -> float:
        """99th percentile latency in milliseconds."""
        return _percentile(sorted(self._durations), 99)

    @property
    def min_ms(self) -> float:
        """Minimum recorded duration."""
        return min(self._durations) if self._durations else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum recorded duration."""
        return max(self._durations) if self._durations else 0.0

    @property
    def mean_ms(self) -> float:
        """Arithmetic mean of recorded durations."""
        if not self._durations:
            return 0.0
        return sum(self._durations) / len(self._durations)

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Return a full statistics dictionary."""
        return {
            "name": self.name,
            "sla_ms": self.sla_ms,
            "count": self.count,
            "violations": self.violations,
            "compliance_rate": round(self.compliance_rate, 6),
            "compliance_pct": round(self.compliance_rate * 100, 2),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "mean_ms": round(self.mean_ms, 3),
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "p99_ms": round(self.p99_ms, 3),
        }

    def reset(self) -> None:
        """Clear all recorded data."""
        self._durations = []
        self._violations_count = 0

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"SLATracker(name={self.name!r}, sla_ms={self.sla_ms}, "
            f"count={self.count}, compliance={self.compliance_rate:.1%})"
        )
