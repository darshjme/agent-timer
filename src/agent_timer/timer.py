"""High-precision execution timer using time.perf_counter."""

import time
from typing import Optional


class Timer:
    """
    High-precision execution timer.

    Usage::

        # Manual start/stop
        t = Timer()
        t.start()
        do_work()
        elapsed = t.stop()  # ms

        # Context manager
        with Timer() as t:
            do_work()
        print(t.elapsed_ms)

        # Fluent
        t = Timer().start()
    """

    def __init__(self) -> None:
        self._start_time: Optional[float] = None  # perf_counter value
        self._elapsed: float = 0.0  # accumulated ms (when stopped)
        self._running: bool = False

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def start(self) -> "Timer":
        """Start (or resume) the timer. Returns self for fluent chaining."""
        self._start_time = time.perf_counter()
        self._running = True
        return self

    def stop(self) -> float:
        """Stop the timer and return total elapsed milliseconds."""
        if self._running and self._start_time is not None:
            self._elapsed += (time.perf_counter() - self._start_time) * 1000.0
            self._running = False
            self._start_time = None
        return self._elapsed

    def reset(self) -> "Timer":
        """Reset the timer to zero. Returns self."""
        self._start_time = None
        self._elapsed = 0.0
        self._running = False
        return self

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def elapsed_ms(self) -> float:
        """Current elapsed time in milliseconds (works while running)."""
        if self._running and self._start_time is not None:
            return self._elapsed + (time.perf_counter() - self._start_time) * 1000.0
        return self._elapsed

    @property
    def elapsed_seconds(self) -> float:
        """Current elapsed time in seconds (works while running)."""
        return self.elapsed_ms / 1000.0

    @property
    def is_running(self) -> bool:
        """True if the timer is currently running."""
        return self._running

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        state = "running" if self._running else "stopped"
        return f"Timer({state}, elapsed_ms={self.elapsed_ms:.3f})"
