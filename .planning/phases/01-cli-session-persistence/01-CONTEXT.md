# Phase 1: CLI Session Persistence - Context

**Gathered:** 2026-06-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase makes CitrusButter CLI session events persist by default as JSONL audit logs. It covers CLI wiring for `citrus run` and `citrus chat`, directory selection, disabling persistence, and explicit session ID selection. It does not add replay, memory extraction, context restoration, config-file support, environment-variable support, or UI/TUI viewing.

</domain>

<decisions>
## Implementation Decisions

### Session Product Intent
- **D-01:** Session persistence is a durable audit trail. It records what happened during a run or chat session for debugging, inspection, and future replay/eval work.
- **D-02:** Session persistence is not automatic model context recovery and is not long-term memory. Active chat context remains managed through `RunResult.messages`; future selected recall belongs behind `ContextSource` or `MemoryService`.

### Default CLI Behavior
- **D-03:** `citrus run` and `citrus chat` both write session logs by default.
- **D-04:** The default session log directory is `.citrus/sessions/`, producing files shaped like `.citrus/sessions/{session_id}.jsonl`.

### User Controls
- **D-05:** Add CLI flags only for Phase 1. Do not extend `config.toml` or environment variable precedence in this phase.
- **D-06:** Add `--session-dir PATH` to override the default session log directory.
- **D-07:** Add `--no-session-log` to disable persistent logging and use `InMemorySessionStore`.
- **D-08:** Add `--session-id ID` for both `run` and `chat`, allowing users to choose the JSONL filename and correlate logs in scripts or debugging sessions.

### the agent's Discretion
The planner may choose exact helper function names and internal CLI plumbing as long as the public behavior above is preserved and `AgentRuntime` remains unchanged.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning Context
- `.planning/PROJECT.md` — Project constraints and locked architecture decisions.
- `.planning/REQUIREMENTS.md` — Requirement `SESS-01` and current milestone traceability.
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria.

### Architecture And Session Boundaries
- `docs/ADR/0001-runtime-kernel.md` — `AgentRuntime` owns the loop; CLI is a client of the SDK.
- `docs/ADR/0002-memory-boundary.md` — Session history, active context, and memory are separate concepts.
- `docs/V1_ARCHITECTURE.md` — Existing V1 CLI/runtime/session architecture and the known gap that CLI uses in-memory sessions.
- `docs/ROADMAP.md` — Product roadmap entry for exposing JSONL persistence through the CLI.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/citrus/sessions/jsonl.py`: `JsonlSessionStore` already appends and loads `SessionEvent` JSONL files by `session_id`.
- `src/citrus/sessions/memory.py`: `InMemorySessionStore` remains the fallback when persistence is disabled.
- `src/citrus/runtime/agent.py`: `RunRequest.session_id` already lets callers choose a session ID; runtime emits events through the injected `SessionStore`.

### Established Patterns
- `src/citrus/cli/app.py`: `_build_runtime()` currently constructs the runtime and hardcodes `InMemorySessionStore()`. This is the natural integration point for selecting a session store.
- `src/citrus/cli/app.py`: `run` and `chat` are Typer commands with explicit option parameters, matching the decision to add CLI flags only.
- `tests/test_cli.py`: CLI behavior is tested with `CliRunner`, monkeypatching, and temporary directories.
- `tests/test_sessions.py`: JSONL store round-trip behavior is already covered at the storage layer.

### Integration Points
- Add session-store selection near `_build_runtime()` or a small helper it calls.
- Pass `session_id` into `RunRequest` from both `run` and `chat`.
- Keep provider selection, permission approval, context building, and runtime loop behavior unchanged.

</code_context>

<specifics>
## Specific Ideas

Expected CLI behavior:

- `citrus run "task"` writes `.citrus/sessions/{generated_session_id}.jsonl`.
- `citrus chat` writes one session log for the interactive chat session unless the user supplies a specific `--session-id`.
- `--session-dir PATH` changes the output directory.
- `--no-session-log` keeps the current in-memory behavior.
- `--session-id ID` chooses the session ID for `run` and `chat`.

</specifics>

<deferred>
## Deferred Ideas

- Config-file and environment-variable session settings are deferred.
- Replay, trace viewing, eval fixture generation, and session analytics are deferred.
- Automatic chat context restoration from JSONL is deferred and should not be implied by this phase.

</deferred>

---

*Phase: 1-CLI Session Persistence*
*Context gathered: 2026-06-22*
