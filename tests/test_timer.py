"""Tests for Timer — uses mock perf_counter to avoid slow sleeps."""

import time
from unittest.mock import patch

import pytest

from agent_timer import Timer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_perf_counter(values):
    """Returns a callable that pops from a list of perf_counter values."""
    it = iter(values)
    def _counter():
        return next(it)
    return _counter


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTimerBasic:
    def test_initial_state_not_running(self):
        t = Timer()
        assert not t.is_running
        assert t.elapsed_ms == 0.0
        assert t.elapsed_seconds == 0.0

    def test_start_returns_self(self):
        t = Timer()
        result = t.start()
        assert result is t
        t.stop()

    def test_stop_returns_elapsed(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.5]  # 0 → start, 0.5 → stop
            t = Timer()
            t.start()
            elapsed = t.stop()
        assert elapsed == pytest.approx(500.0, abs=0.01)  # 0.5s → 500ms

    def test_elapsed_ms_while_running(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.123]
            t = Timer()
            t.start()
            assert t.elapsed_ms == pytest.approx(123.0, abs=0.01)

    def test_elapsed_seconds_convenience(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 1.0]
            t = Timer()
            t.start()
            assert t.elapsed_seconds == pytest.approx(1.0, abs=0.001)

    def test_stop_sets_not_running(self):
        t = Timer()
        t.start()
        t.stop()
        assert not t.is_running

    def test_stop_twice_is_idempotent(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.2]
            t = Timer()
            t.start()
            first = t.stop()
            second = t.stop()
        assert first == second

    def test_reset_clears_elapsed(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.3]
            t = Timer()
            t.start()
            t.stop()
        t.reset()
        assert t.elapsed_ms == 0.0
        assert not t.is_running

    def test_reset_returns_self(self):
        t = Timer()
        assert t.reset() is t

    def test_context_manager_start_stop(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.05]
            with Timer() as t:
                pass
        assert t.elapsed_ms == pytest.approx(50.0, abs=0.01)
        assert not t.is_running

    def test_elapsed_ms_after_stop(self):
        with patch("agent_timer.timer.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.4]
            t = Timer()
            t.start()
            t.stop()
        # After stop, elapsed_ms should be stable (no more mock values needed)
        assert t.elapsed_ms == pytest.approx(400.0, abs=0.01)

    def test_repr_contains_state(self):
        t = Timer()
        t.start()
        r = repr(t)
        assert "running" in r
        t.stop()
        assert "stopped" in repr(t)
