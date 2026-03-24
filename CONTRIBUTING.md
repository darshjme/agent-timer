# Contributing to agent-timer

Thank you for your interest in contributing! This document explains how to get started.

## Development Setup

```bash
git clone https://github.com/example/agent-timer.git
cd agent-timer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All tests must pass before submitting a PR. No `time.sleep` calls longer than 10 ms in tests — use mock time instead.

## Code Style

- Python 3.10+ type hints throughout
- Docstrings on every public class and method
- Zero external runtime dependencies (stdlib only)
- `time.perf_counter` for all timing (not `time.time`)

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests for your changes
4. Ensure all tests pass
5. Open a Pull Request with a clear description

## Reporting Bugs

Open an issue with:
- Python version and OS
- Minimal reproducible example
- Expected vs actual behaviour

## Design Principles

- **Zero deps** — stdlib only; no numpy, no third-party packages
- **High precision** — always use `time.perf_counter`
- **Fast tests** — no slow sleeps; mock time when needed
- **Agent-first** — every feature must solve a real LLM agent timing problem
