"""Multi-step profiler for LLM agent pipelines."""

import time
from contextlib import contextmanager
from typing import Any, Generator, Optional


class StepNotStartedError(Exception):
    """Raised when end_step is called for a step that was never started."""


class StepAlreadyStartedError(Exception):
    """Raised when start_step is called for a step already in progress."""


class _StepRecord:
    """Internal record for a single named step."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: Optional[float] = None
        self._elapsed_ms: float = 0.0
        self._running: bool = False
        self.call_count: int = 0

    def start(self) -> None:
        if self._running:
            raise StepAlreadyStartedError(
                f"Step {self.name!r} is already running"
            )
        self._start = time.perf_counter()
        self._running = True

    def end(self) -> float:
        if not self._running or self._start is None:
            raise StepNotStartedError(
                f"Step {self.name!r} was not started"
            )
        self._elapsed_ms += (time.perf_counter() - self._start) * 1000.0
        self._running = False
        self._start = None
        self.call_count += 1
        return self._elapsed_ms

    @property
    def elapsed_ms(self) -> float:
        if self._running and self._start is not None:
            return self._elapsed_ms + (time.perf_counter() - self._start) * 1000.0
        return self._elapsed_ms

    @property
    def is_running(self) -> bool:
        return self._running


class Profiler:
    """
    Multi-step profiler for tracing individual stages of an agent pipeline.

    Usage::

        profiler = Profiler("rag-pipeline")
        profiler.start_step("embed")
        ...
        profiler.end_step("embed")

        with profiler.step("llm-call"):
            response = llm(prompt)

        print(profiler.report())
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: dict[str, _StepRecord] = {}
        self._order: list[str] = []  # insertion order

    # ------------------------------------------------------------------
    # Manual step control
    # ------------------------------------------------------------------

    def start_step(self, step_name: str) -> None:
        """Start timing a named step."""
        if step_name not in self._steps:
            self._steps[step_name] = _StepRecord(step_name)
            self._order.append(step_name)
        self._steps[step_name].start()

    def end_step(self, step_name: str) -> float:
        """End timing a named step. Returns elapsed ms for that step."""
        if step_name not in self._steps:
            raise StepNotStartedError(
                f"Step {step_name!r} has not been started"
            )
        return self._steps[step_name].end()

    # ------------------------------------------------------------------
    # Context manager per step
    # ------------------------------------------------------------------

    @contextmanager
    def step(self, step_name: str) -> Generator[_StepRecord, None, None]:
        """
        Context manager for a named step::

            with profiler.step("llm-call") as s:
                ...
            # s.elapsed_ms available after the block
        """
        self.start_step(step_name)
        record = self._steps[step_name]
        try:
            yield record
        finally:
            self.end_step(step_name)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    @property
    def total_ms(self) -> float:
        """Sum of all completed (non-running) step durations."""
        return sum(r.elapsed_ms for r in self._steps.values())

    def report(self) -> dict[str, Any]:
        """
        Return a full profiling report dictionary::

            {
              "profiler": "rag-pipeline",
              "total_ms": 312.4,
              "steps": {
                "embed": {"elapsed_ms": 45.2, "pct": 14.5, "calls": 1},
                ...
              }
            }
        """
        total = self.total_ms
        steps: dict[str, Any] = {}
        for name in self._order:
            rec = self._steps[name]
            ms = rec.elapsed_ms
            pct = (ms / total * 100.0) if total > 0 else 0.0
            steps[name] = {
                "elapsed_ms": round(ms, 3),
                "pct": round(pct, 2),
                "calls": rec.call_count,
            }
        return {
            "profiler": self.name,
            "total_ms": round(total, 3),
            "steps": steps,
        }

    def reset(self) -> None:
        """Clear all step data."""
        self._steps.clear()
        self._order.clear()

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Profiler(name={self.name!r}, steps={list(self._order)}, "
            f"total_ms={self.total_ms:.3f})"
        )
