---
phase: 01
slug: cli-session-persistence
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-22
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_cli.py tests/test_sessions.py` |
| **Full suite command** | `env PYTHONPATH=src .venv/bin/python -m pytest -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_cli.py tests/test_sessions.py`
- **After every plan wave:** Run `env PYTHONPATH=src .venv/bin/python -m pytest -q`
- **Before `$gsd-verify-work`:** Full suite, ruff, and mypy must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SESS-01 | T-01-01 | Session files stay under user-selected/default directory | CLI integration | `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_cli.py tests/test_sessions.py` | yes | pending |
| 01-01-02 | 01 | 1 | SESS-01 | T-01-02 | `--no-session-log` avoids persistent writes | CLI integration | `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_cli.py tests/test_sessions.py` | yes | pending |
| 01-01-03 | 01 | 1 | SESS-01 | — | README documents exact CLI flags | docs/source | `rg -- '--session-dir|--no-session-log|--session-id' README.md` | yes | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements:

- `tests/test_cli.py` exists.
- `tests/test_sessions.py` exists.
- `pyproject.toml` configures pytest, ruff, and mypy.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 10 seconds
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-22
