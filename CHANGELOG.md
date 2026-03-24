# Changelog

All notable changes to **agent-timer** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2024-03-01

### Added
- `Timer` — high-precision execution timer using `time.perf_counter`
  - `start()`, `stop()`, `reset()`, `elapsed_ms`, `elapsed_seconds`
  - Context manager support (`with Timer() as t:`)
- `DeadlineTimer` — countdown timer with deadline enforcement
  - `remaining_ms`, `is_expired`, `check()`
  - `DeadlineExceededError` with over-budget details
  - Context manager: raises on exit if deadline exceeded
- `SLATracker` — compliance tracker over multiple calls
  - `record()`, `compliance_rate`, `violations`
  - `p50_ms`, `p95_ms`, `p99_ms` (pure-Python percentiles)
  - `stats()` dictionary, `reset()`
  - `SLAViolationError`
- `@timed` decorator — automatic timing for sync and async functions
  - JSON stdout logging
  - `sla_ms` enforcement, `tracker` recording, `log` control
- `Profiler` — multi-step pipeline profiling
  - `start_step()` / `end_step()` manual control
  - `with profiler.step("name"):` context manager
  - `report()` with per-step `elapsed_ms`, `pct`, and `calls`
- Zero external runtime dependencies; uses only Python stdlib
- Full pytest test suite (22+ tests)

[Unreleased]: https://github.com/example/agent-timer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/example/agent-timer/releases/tag/v0.1.0
