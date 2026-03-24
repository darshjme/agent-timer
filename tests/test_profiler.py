"""Tests for Profiler — multi-step pipeline timing."""

from unittest.mock import patch

import pytest

from agent_timer import Profiler
from agent_timer.profiler import StepNotStartedError, StepAlreadyStartedError


class TestProfiler:
    def test_basic_start_end(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1]
            p = Profiler("pipe")
            p.start_step("step1")
            p.end_step("step1")
        report = p.report()
        assert "step1" in report["steps"]
        assert report["steps"]["step1"]["elapsed_ms"] == pytest.approx(100.0, abs=0.1)

    def test_report_total_ms(self):
        with patch("agent_timer.profiler.time") as mock_time:
            # start step1, end step1, start step2, end step2
            mock_time.perf_counter.side_effect = [0.0, 0.1, 0.0, 0.2]
            p = Profiler("pipe")
            p.start_step("a")
            p.end_step("a")
            p.start_step("b")
            p.end_step("b")
        report = p.report()
        assert report["total_ms"] == pytest.approx(300.0, abs=0.1)

    def test_report_pct_sums_to_100(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1, 0.0, 0.3]
            p = Profiler("pipe")
            p.start_step("a")
            p.end_step("a")
            p.start_step("b")
            p.end_step("b")
        report = p.report()
        total_pct = sum(v["pct"] for v in report["steps"].values())
        assert total_pct == pytest.approx(100.0, abs=0.01)

    def test_context_manager_step(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.05]
            p = Profiler("pipe")
            with p.step("llm-call") as s:
                pass
        report = p.report()
        assert "llm-call" in report["steps"]
        assert report["steps"]["llm-call"]["elapsed_ms"] == pytest.approx(50.0, abs=0.1)

    def test_context_manager_yields_step_record(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.2, 0.2]
            p = Profiler("pipe")
            with p.step("fetch") as s:
                _ = s.elapsed_ms  # should not raise

    def test_end_step_not_started_raises(self):
        p = Profiler("pipe")
        with pytest.raises(StepNotStartedError):
            p.end_step("ghost")

    def test_start_step_twice_raises(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0]
            p = Profiler("pipe")
            p.start_step("s")
            with pytest.raises(StepAlreadyStartedError):
                p.start_step("s")

    def test_report_preserves_insertion_order(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1, 0.0, 0.1, 0.0, 0.1]
            p = Profiler("pipe")
            for name in ["z", "a", "m"]:
                p.start_step(name)
                p.end_step(name)
        assert list(p.report()["steps"].keys()) == ["z", "a", "m"]

    def test_reset_clears_steps(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1]
            p = Profiler("pipe")
            p.start_step("s")
            p.end_step("s")
        p.reset()
        assert p.report()["steps"] == {}
        assert p.total_ms == 0.0

    def test_calls_count(self):
        with patch("agent_timer.profiler.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1, 0.0, 0.1]
            p = Profiler("pipe")
            p.start_step("s")
            p.end_step("s")
            p.start_step("s")
            p.end_step("s")
        assert p.report()["steps"]["s"]["calls"] == 2

    def test_repr(self):
        p = Profiler("my-pipe")
        r = repr(p)
        assert "my-pipe" in r

    def test_report_profiler_name(self):
        p = Profiler("rag-v2")
        assert p.report()["profiler"] == "rag-v2"
