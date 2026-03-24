"""Tests for the @timed decorator — sync and async, SLA, tracker, logging."""

import asyncio
import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from agent_timer import timed, SLATracker
from agent_timer.sla import SLAViolationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def capture_stdout(func, *args, **kwargs):
    """Run func and capture its stdout output."""
    buf = StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        result = func(*args, **kwargs)
    finally:
        sys.stdout = old
    return result, buf.getvalue()


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------

class TestTimedSync:
    def test_bare_decorator_logs_json(self):
        @timed
        def work():
            return 42

        result, out = capture_stdout(work)
        assert result == 42
        data = json.loads(out.strip())
        assert data["event"] == "timed"
        assert "elapsed_ms" in data
        assert data["elapsed_ms"] >= 0

    def test_decorator_with_parens_logs_json(self):
        @timed()
        def work():
            return "hello"

        result, out = capture_stdout(work)
        assert result == "hello"
        data = json.loads(out.strip())
        assert data["event"] == "timed"

    def test_sla_ok_no_raise(self):
        """Function that completes quickly should not raise SLAViolationError."""
        @timed(sla_ms=10_000)  # very generous SLA
        def fast():
            return True

        result, out = capture_stdout(fast)
        assert result is True
        data = json.loads(out.strip())
        assert data["sla_ok"] is True

    def test_sla_violation_raises(self):
        """Mock the timer to simulate exceeding the SLA."""
        call_count = [0]
        original_perf = __import__("time").perf_counter

        def fake_perf():
            call_count[0] += 1
            if call_count[0] == 1:
                return 0.0
            return 2.0  # 2000ms elapsed

        @timed(sla_ms=500, log=False)
        def slow():
            pass

        with patch("agent_timer.decorator.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 2.0]
            with pytest.raises(SLAViolationError) as exc_info:
                slow()
        assert exc_info.value.sla_ms == 500
        assert exc_info.value.elapsed_ms == pytest.approx(2000.0, abs=1)

    def test_tracker_records_duration(self):
        tracker = SLATracker("test", sla_ms=10_000)

        @timed(tracker=tracker, log=False)
        def work():
            return 99

        work()
        work()
        assert tracker.count == 2

    def test_log_false_no_stdout(self):
        @timed(log=False)
        def quiet():
            return "silent"

        result, out = capture_stdout(quiet)
        assert result == "silent"
        assert out == ""

    def test_preserves_function_name(self):
        @timed
        def my_special_function():
            pass

        assert my_special_function.__name__ == "my_special_function"

    def test_passes_args_and_kwargs(self):
        @timed(log=False)
        def add(a, b, *, c=0):
            return a + b + c

        assert add(1, 2, c=3) == 6


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------

class TestTimedAsync:
    @pytest.mark.asyncio
    async def test_async_bare_decorator_logs_json(self):
        @timed
        async def async_work():
            return "async"

        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            result = await async_work()
        finally:
            sys.stdout = old

        assert result == "async"
        data = json.loads(buf.getvalue().strip())
        assert data["event"] == "timed"

    @pytest.mark.asyncio
    async def test_async_sla_ok(self):
        @timed(sla_ms=10_000, log=False)
        async def fast_async():
            return True

        result = await fast_async()
        assert result is True

    @pytest.mark.asyncio
    async def test_async_sla_violation(self):
        @timed(sla_ms=1, log=False)
        async def always_slow():
            await asyncio.sleep(0.005)  # 5ms > 1ms SLA

        with pytest.raises(SLAViolationError):
            await always_slow()

    @pytest.mark.asyncio
    async def test_async_tracker(self):
        tracker = SLATracker("async-tracker", sla_ms=10_000)

        @timed(tracker=tracker, log=False)
        async def async_op():
            return 1

        await async_op()
        await async_op()
        assert tracker.count == 2
