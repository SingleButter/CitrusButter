---
phase: 01
slug: cli-session-persistence
status: complete
created: 2026-06-22
---

# Phase 1 Research: CLI Session Persistence

## Research Complete

Phase 1 can be planned from existing code. The SDK already has the storage boundary and JSONL implementation; the missing work is CLI wiring, tests, and documentation.

## Current Code Findings

### Existing Session Boundary

- `src/citrus/runtime/agent.py` accepts a `SessionStore` dependency and emits structured `SessionEvent` records through `_emit`.
- `RunRequest.session_id` already lets callers supply a stable ID; if omitted, `AgentRuntime` generates a UUID.
- `src/citrus/sessions/base.py` defines the store protocol.
- `src/citrus/sessions/memory.py` is the current CLI behavior via `InMemorySessionStore`.
- `src/citrus/sessions/jsonl.py` already creates a directory and writes `{session_id}.jsonl` with one JSON event per line.

### CLI Integration Point

- `src/citrus/cli/app.py` has `_build_runtime(selected_provider)` hardcoded to `InMemorySessionStore()`.
- `run()` calls `runtime.run(RunRequest(task=task))`.
- `chat()` creates one runtime, maintains active `messages`, and calls `runtime.run(RunRequest(task=task, messages=messages))` for each turn.
- Phase 1 should add session-store selection without changing `AgentRuntime`.

### Test Patterns

- `tests/test_cli.py` uses `CliRunner`, `monkeypatch.chdir(tmp_path)`, fake providers, and filesystem assertions.
- `tests/test_sessions.py` already verifies `JsonlSessionStore` round-trips events.
- New CLI tests should verify files exist and contain expected event types rather than duplicating storage round-trip tests.

### Documentation Context

- `README.md` already says the next practical step is to add a CLI option such as `--session-dir .citrus/sessions`.
- Docs and GSD context now refine that into default persistence plus CLI-only controls.

## Recommended Implementation Approach

1. Add `JsonlSessionStore` import and a helper such as `_build_session_store(session_dir, no_session_log)`.
2. Add shared Typer options to `run()` and `chat()`:
   - `--session-dir PATH`
   - `--no-session-log`
   - `--session-id ID`
3. Default session directory should be `Path(".citrus/sessions")`.
4. Pass the selected session store into `_build_runtime`.
5. Pass `session_id` into `RunRequest` for both `run` and `chat`.
6. For `chat`, keep the same `session_id` for all turns so one interactive session writes one JSONL file.
7. Do not add config-file or environment-variable support in this phase.

## Edge Cases To Cover

- Default `citrus run` writes `.citrus/sessions/{generated_id}.jsonl`.
- `--session-id fixed` writes `.citrus/sessions/fixed.jsonl`.
- `--session-dir custom` writes to the supplied directory.
- `--no-session-log` does not create `.citrus/sessions`.
- `citrus chat --session-id chat-1` appends multiple turns to `.citrus/sessions/chat-1.jsonl`.
- Existing permission prompt and chat context tests continue to pass.

## Validation Architecture

The existing pytest suite is sufficient. Phase verification should use:

- Quick command: `env PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_cli.py tests/test_sessions.py`
- Full command: `env PYTHONPATH=src .venv/bin/python -m pytest -q`
- Lint command: `env PYTHONPATH=src .venv/bin/python -m ruff check src tests`
- Type command: `env PYTHONPATH=src .venv/bin/python -m mypy src`

All Phase 1 behaviors can be automated with CLI tests; no manual verification is required.

## Out Of Scope

- Config-file or environment-variable session settings.
- Replay commands, trace viewers, and eval fixture generation.
- Automatic context restoration from JSONL logs.
- Memory extraction from sessions.
