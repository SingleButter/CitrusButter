---
phase: 01
slug: cli-session-persistence
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-22
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI flags to local filesystem | User-provided CLI options select whether and where session logs are written. | `--session-dir`, `--no-session-log`, and `--session-id` values; local path and filename selection. |
| Runtime events to JSONL audit log | Structured runtime events are persisted from `AgentRuntime` through the injected `SessionStore`. | Task text, event metadata, final messages, tool-request metadata, and other local audit data. |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Tampering / path confusion | CLI session directory selection | mitigate | `--session-dir` is treated as an explicit `Path` and passed directly to `JsonlSessionStore`; no shell interpolation or implicit command execution is introduced. CLI tests use `tmp_path` and assert logs are created only in the expected default or custom directory. | closed |
| T-01-02 | Information disclosure | JSONL session audit logs | mitigate | README describes session logs as local audit artifacts, explicitly says they do not restore active context or act as memory, and warns that `.citrus/` is gitignored because local config and logs may contain sensitive data. `.gitignore` ignores `.citrus/`. | closed |

---

## Verification Evidence

| Threat ID | Evidence |
|-----------|----------|
| T-01-01 | `src/citrus/cli/app.py` contains `JsonlSessionStore(session_dir or Path(".citrus/sessions"))`, `--session-dir`, `--no-session-log`, and `--session-id`; `tests/test_cli.py` covers default logging, custom directory logging, and disabled persistent output. |
| T-01-02 | `README.md` documents `.citrus/sessions/{session_id}.jsonl`, identifies logs as audit history, states they do not automatically restore active chat context or act as long-term memory, and `.gitignore` contains `.citrus/`. |

Verification commands run:

- `rg -n "session_dir|JsonlSessionStore|Path\\(\"\\.citrus/sessions\"\\)|--session-dir|--no-session-log|--session-id|shell|subprocess|os\\.system" src/citrus/cli/app.py`
- `rg -n "custom-sessions|off-1|run-1.jsonl|chat-1.jsonl|session-dir|no-session-log" tests/test_cli.py`
- `rg -n "\\.citrus/|audit|sensitive|restore active chat context|long-term memory|--session-dir|--no-session-log|--session-id" README.md .gitignore`
- `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_cli.py tests/test_sessions.py`

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-22 | 2 | 2 | 0 | Codex |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-22
