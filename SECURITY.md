# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes     |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing the maintainers directly (see `pyproject.toml` for contact).

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional but appreciated)

We will acknowledge your report within 48 hours and aim to release a patch within 7 days for critical issues.

## Scope

`agent-timer` is a pure-Python timing library with zero external dependencies and no network I/O, no file I/O (beyond optional stdout logging), and no cryptographic operations. Its attack surface is minimal.

Potential concerns include:
- **Denial-of-service via resource exhaustion** — e.g., recording unbounded numbers of samples into `SLATracker`; callers are responsible for bounding input size.
- **Timing side-channels** — this library measures elapsed time; in security-sensitive contexts, callers must treat timing data as potentially sensitive.
