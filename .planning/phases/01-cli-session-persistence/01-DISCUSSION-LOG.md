# Phase 1: CLI Session Persistence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-22
**Phase:** 1-CLI Session Persistence
**Areas discussed:** Session product intent, Default CLI behavior, User controls, Session identity controls

---

## Session Product Intent

| Option | Description | Selected |
|--------|-------------|----------|
| Durable audit trail | Persist event logs for debugging, inspection, and future replay/eval; keep separate from active context and memory. | yes |
| Context recovery mechanism | Treat session logs as automatic model context restoration. | |
| Memory mechanism | Treat session logs as durable facts to inject into future prompts. | |

**User's choice:** The user asked what the session part should ultimately achieve; the clarified target was durable audit trail.
**Notes:** Active context remains `RunResult.messages`; memory remains separate.

---

## Default CLI Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Opt-in only | Only write JSONL when `--session-dir` is passed. | |
| Project default | Default to `.citrus/sessions/` and provide a way to disable logging. | yes |
| Hybrid | Default only for chat, opt-in for run. | |

**User's choice:** Project default.
**Notes:** Default output path should be `.citrus/sessions/{session_id}.jsonl`.

---

## Command Coverage

| Option | Description | Selected |
|--------|-------------|----------|
| `run` and `chat` both default to persistent session logs | Consistent behavior and full CLI audit trail. | yes |
| Only `chat` defaults to persistent session logs | Fewer one-shot files, weaker audit trail for `run`. | |
| Only `run` first | Smaller implementation, less aligned with session goal. | |

**User's choice:** `run` and `chat` both default to persistent session logs.
**Notes:** `chat` should use one session ID across the interactive loop.

---

## User Controls

| Option | Description | Selected |
|--------|-------------|----------|
| CLI flags only | Add `--session-dir` and `--no-session-log`; do not extend config/env. | yes |
| CLI flags plus env var | Add `CITRUS_SESSION_DIR` for scripts/CI. | |
| CLI flags plus config and env | Add full precedence behavior now. | |

**User's choice:** CLI flags only.
**Notes:** Keeps Phase 1 narrow and avoids expanding config precedence.

---

## Session Identity Controls

| Option | Description | Selected |
|--------|-------------|----------|
| Add `--session-id` | Let both `run` and `chat` choose the session ID for reproducible logs. | yes |
| No `--session-id` | Runtime-generated UUID only. | |
| `chat` only | Session ID control only for long-running interactive sessions. | |

**User's choice:** Add `--session-id` for both `run` and `chat`.
**Notes:** This aligns with debugging and scriptability while using existing `RunRequest.session_id`.

---

## the agent's Discretion

- Exact helper function names and internal CLI plumbing are left to the planner/executor.
- The implementation should preserve the public behavior and avoid changing `AgentRuntime`.

## Deferred Ideas

- Config-file and environment-variable session settings.
- Replay, trace viewing, eval fixture generation, and session analytics.
- Automatic chat context restoration from JSONL.
