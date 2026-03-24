"""Tests for DeadlineTimer."""

from unittest.mock import patch

import pytest

from agent_timer import DeadlineTimer, DeadlineExceededError


class TestDeadlineTimer:
    def test_not_expired_within_deadline(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1]  # 100ms elapsed
            d = DeadlineTimer(500.0)
            assert not d.is_expired

    def test_expired_past_deadline(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.6]  # 600ms elapsed > 500ms
            d = DeadlineTimer(500.0)
            assert d.is_expired

    def test_remaining_ms_positive(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1]
            d = DeadlineTimer(500.0)
            assert d.remaining_ms == pytest.approx(400.0, abs=0.01)

    def test_remaining_ms_negative_when_expired(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.6]
            d = DeadlineTimer(500.0)
            assert d.remaining_ms < 0

    def test_check_does_not_raise_within_deadline(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1, 0.1]
            d = DeadlineTimer(500.0)
            d.check()  # should not raise

    def test_check_raises_after_deadline(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.6, 0.6]
            d = DeadlineTimer(500.0)
            with pytest.raises(DeadlineExceededError) as exc_info:
                d.check()
        assert "exceeded" in str(exc_info.value).lower()
        assert exc_info.value.deadline_ms == 500.0

    def test_context_manager_raises_on_exit_if_expired(self):
        with patch("agent_timer.deadline.time") as mock_time:
            # start=0.0, then elapsed check on __exit__ = 0.6s → expired
            mock_time.perf_counter.side_effect = [0.0, 0.6, 0.6]
            with pytest.raises(DeadlineExceededError):
                with DeadlineTimer(500.0):
                    pass

    def test_context_manager_no_raise_within_deadline(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1, 0.1]
            with DeadlineTimer(500.0):
                pass  # should not raise

    def test_context_manager_does_not_suppress_other_exceptions(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0]
            with pytest.raises(ValueError):
                with DeadlineTimer(500.0):
                    raise ValueError("other error")

    def test_invalid_deadline_raises(self):
        with pytest.raises(ValueError):
            DeadlineTimer(-1.0)
        with pytest.raises(ValueError):
            DeadlineTimer(0.0)

    def test_repr(self):
        with patch("agent_timer.deadline.time") as mock_time:
            mock_time.perf_counter.side_effect = [0.0, 0.1]
            d = DeadlineTimer(500.0)
            r = repr(d)
        assert "500" in r
