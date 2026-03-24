"""Countdown timer with deadline enforcement."""

import time


class DeadlineExceededError(Exception):
    """Raised when a deadline has been exceeded."""

    def __init__(self, deadline_ms: float, elapsed_ms: float) -> None:
        self.deadline_ms = deadline_ms
        self.elapsed_ms = elapsed_ms
        over_ms = elapsed_ms - deadline_ms
        super().__init__(
            f"Deadline of {deadline_ms:.1f} ms exceeded by {over_ms:.1f} ms "
            f"(elapsed={elapsed_ms:.1f} ms)"
        )


class DeadlineTimer:
    """
    Countdown timer that tracks whether a deadline has been exceeded.

    Usage::

        # Check programmatically
        d = DeadlineTimer(5000)
        while not d.is_expired:
            step()
            d.check()  # raises DeadlineExceededError if over

        # Context manager — raises on __exit__ if deadline passed
        with DeadlineTimer(500) as d:
            do_work()
            print(d.remaining_ms)
    """

    def __init__(self, deadline_ms: float) -> None:
        if deadline_ms <= 0:
            raise ValueError(f"deadline_ms must be positive, got {deadline_ms}")
        self.deadline_ms = deadline_ms
        self._start_time: float = time.perf_counter()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds elapsed since creation."""
        return (time.perf_counter() - self._start_time) * 1000.0

    @property
    def remaining_ms(self) -> float:
        """Milliseconds remaining before deadline (may be negative if expired)."""
        return self.deadline_ms - self.elapsed_ms

    @property
    def is_expired(self) -> bool:
        """True if the deadline has been exceeded."""
        return self.elapsed_ms >= self.deadline_ms

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def check(self) -> None:
        """Raise DeadlineExceededError if the deadline has passed."""
        elapsed = self.elapsed_ms
        if elapsed >= self.deadline_ms:
            raise DeadlineExceededError(self.deadline_ms, elapsed)

    def reset(self) -> "DeadlineTimer":
        """Reset the countdown (new start time, same deadline)."""
        self._start_time = time.perf_counter()
        return self

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DeadlineTimer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Only check deadline if no other exception is propagating
        if exc_type is None:
            self.check()

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        remaining = self.remaining_ms
        state = "EXPIRED" if remaining < 0 else f"remaining={remaining:.1f}ms"
        return f"DeadlineTimer(deadline={self.deadline_ms}ms, {state})"
