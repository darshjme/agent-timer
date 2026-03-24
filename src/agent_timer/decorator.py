"""
@timed decorator — automatic timing for sync and async functions.
Logs JSON to stdout; optionally enforces SLA or records to SLATracker.
"""

import asyncio
import functools
import json
import time
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .sla import SLATracker


class SLAViolationError(Exception):
    """Import from sla module — re-exported here for convenience."""


# Import real SLAViolationError lazily to avoid circular import at module level
def _get_sla_violation_error():
    from .sla import SLAViolationError as E
    return E


def _log_json(func_name: str, elapsed_ms: float, extra: dict | None = None) -> None:
    payload: dict[str, Any] = {
        "event": "timed",
        "function": func_name,
        "elapsed_ms": round(elapsed_ms, 3),
    }
    if extra:
        payload.update(extra)
    print(json.dumps(payload))


def _make_wrapper(
    func: Callable,
    sla_ms: Optional[float],
    tracker: Optional["SLATracker"],
    log: bool,
) -> Callable:
    """Build and return the appropriate wrapper (sync or async)."""

    func_name = f"{func.__module__}.{func.__qualname__}"

    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - t0) * 1000.0
                _handle_result(func_name, elapsed, sla_ms, tracker, log)
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - t0) * 1000.0
                _handle_result(func_name, elapsed, sla_ms, tracker, log)
        return sync_wrapper


def _handle_result(
    func_name: str,
    elapsed_ms: float,
    sla_ms: Optional[float],
    tracker: Optional["SLATracker"],
    log: bool,
) -> None:
    if tracker is not None:
        tracker.record(elapsed_ms)

    if log:
        extra: dict[str, Any] = {}
        if sla_ms is not None:
            extra["sla_ms"] = sla_ms
            extra["sla_ok"] = elapsed_ms <= sla_ms
        _log_json(func_name, elapsed_ms, extra or None)

    if sla_ms is not None and elapsed_ms > sla_ms:
        SLAViolationError_ = _get_sla_violation_error()
        raise SLAViolationError_(func_name, sla_ms, elapsed_ms)


def timed(
    func: Optional[Callable] = None,
    *,
    sla_ms: Optional[float] = None,
    tracker: Optional["SLATracker"] = None,
    log: bool = True,
) -> Callable:
    """
    Decorator for automatic execution timing.

    Forms::

        @timed                           # bare decorator — log only
        @timed()                         # explicit call, same as above
        @timed(sla_ms=500)               # enforce SLA
        @timed(tracker=my_tracker)       # record to SLATracker
        @timed(sla_ms=500, log=False)    # silent SLA enforcement

    Works on both sync and async functions.
    """
    if func is not None:
        # Called as @timed (no parentheses)
        return _make_wrapper(func, sla_ms=None, tracker=None, log=True)

    # Called as @timed(...) — return a decorator
    def decorator(f: Callable) -> Callable:
        return _make_wrapper(f, sla_ms=sla_ms, tracker=tracker, log=log)

    return decorator
