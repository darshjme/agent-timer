"""
agent-timer — execution timing and SLA enforcement for LLM agents.
Zero external dependencies. Uses time.perf_counter for high precision.
"""

from .timer import Timer
from .deadline import DeadlineTimer, DeadlineExceededError
from .sla import SLATracker, SLAViolationError
from .decorator import timed
from .profiler import Profiler

__all__ = [
    "Timer",
    "DeadlineTimer",
    "DeadlineExceededError",
    "SLATracker",
    "SLAViolationError",
    "timed",
    "Profiler",
]

__version__ = "0.1.0"
