"""Tests for SLATracker and SLAViolationError."""

import pytest

from agent_timer import SLATracker
from agent_timer.sla import SLAViolationError, _percentile


class TestPercentile:
    def test_empty_list(self):
        assert _percentile([], 50) == 0.0

    def test_single_element(self):
        assert _percentile([42.0], 95) == 42.0

    def test_median_of_even_list(self):
        data = sorted([10.0, 20.0, 30.0, 40.0])
        assert _percentile(data, 50) == pytest.approx(25.0)

    def test_p100(self):
        data = sorted([1.0, 2.0, 3.0, 4.0, 5.0])
        assert _percentile(data, 100) == 5.0

    def test_p0(self):
        data = sorted([1.0, 2.0, 3.0])
        assert _percentile(data, 0) == 1.0


class TestSLATracker:
    def test_initial_state(self):
        t = SLATracker("test", sla_ms=100.0)
        assert t.count == 0
        assert t.violations == 0
        assert t.compliance_rate == 1.0
        assert t.p50_ms == 0.0

    def test_invalid_sla_raises(self):
        with pytest.raises(ValueError):
            SLATracker("bad", sla_ms=0)
        with pytest.raises(ValueError):
            SLATracker("bad", sla_ms=-5)

    def test_record_within_sla(self):
        t = SLATracker("test", sla_ms=500.0)
        t.record(100.0)
        t.record(200.0)
        assert t.count == 2
        assert t.violations == 0
        assert t.compliance_rate == 1.0

    def test_record_violation(self):
        t = SLATracker("test", sla_ms=100.0)
        t.record(50.0)
        t.record(200.0)  # violation
        assert t.violations == 1
        assert t.compliance_rate == pytest.approx(0.5)

    def test_compliance_rate_all_violations(self):
        t = SLATracker("test", sla_ms=10.0)
        for v in [50.0, 60.0, 70.0]:
            t.record(v)
        assert t.compliance_rate == pytest.approx(0.0)

    def test_p50_p95_p99(self):
        t = SLATracker("test", sla_ms=999.0)
        # 100 values: 1..100
        for v in range(1, 101):
            t.record(float(v))
        assert t.p50_ms == pytest.approx(50.5, abs=0.1)
        assert t.p95_ms == pytest.approx(95.05, abs=0.5)
        assert t.p99_ms == pytest.approx(99.01, abs=0.5)

    def test_min_max_mean(self):
        t = SLATracker("test", sla_ms=999.0)
        for v in [10.0, 20.0, 30.0]:
            t.record(v)
        assert t.min_ms == 10.0
        assert t.max_ms == 30.0
        assert t.mean_ms == pytest.approx(20.0)

    def test_stats_dict_keys(self):
        t = SLATracker("mytracker", sla_ms=200.0)
        t.record(100.0)
        s = t.stats()
        assert s["name"] == "mytracker"
        assert s["sla_ms"] == 200.0
        assert s["count"] == 1
        assert s["violations"] == 0
        assert "compliance_rate" in s
        assert "p50_ms" in s
        assert "p95_ms" in s
        assert "p99_ms" in s

    def test_reset_clears_data(self):
        t = SLATracker("test", sla_ms=100.0)
        t.record(50.0)
        t.record(200.0)
        t.reset()
        assert t.count == 0
        assert t.violations == 0
        assert t.compliance_rate == 1.0

    def test_repr(self):
        t = SLATracker("mytracker", sla_ms=500.0)
        t.record(300.0)
        r = repr(t)
        assert "mytracker" in r
        assert "500" in r
