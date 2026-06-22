# Requirements: CitrusButter

**Defined:** 2026-06-22
**Core Value:** Keep `AgentRuntime` as the stable owner of the agent loop while every major capability remains replaceable at a narrow boundary.

## v1 Requirements

Requirements for the current GSD-managed milestone. Product V1 and core V2 are already validated in `PROJECT.md`; this milestone covers the next executable work.

### Session Persistence

- [x] **SESS-01**: CLI users can persist sessions to JSONL through an option or default `.citrus/sessions/` directory.

### Context Sources And Compaction

- [ ] **CTX-01**: CitrusButter exposes a `ContextSource` extension boundary for repo summaries, project rules, selected memory notes, and future contextual inputs.
- [ ] **CTX-02**: `ContextBuilder` can retrieve selected context source output and place it into active messages without changing `AgentRuntime`.
- [ ] **CTX-03**: Context compaction can optionally use provider-aware token budgeting while preserving valid assistant tool-call/tool-result sequences.
- [ ] **CTX-04**: Context compaction can optionally use LLM summary compaction or a layered compaction pipeline behind the same compactor boundary.

### External Tools And MCP

- [ ] **MCP-01**: CitrusButter implements `MCPToolSource` without moving MCP-specific logic into `AgentRuntime`.
- [ ] **MCP-02**: CitrusButter supports MCP server configuration using the existing configuration boundary.
- [ ] **MCP-03**: MCP tools are normalized into standard CitrusButter `Tool` objects.
- [ ] **MCP-04**: Contract tests prove MCP tools and local tools share the same execution and permission path.

## v2 Requirements

Deferred to future milestones.

### Workspace Safety

- **SAFE-01**: Add workspace policy for allowed paths.
- **SAFE-02**: Add safer shell execution profiles.
- **SAFE-03**: Consider git worktree or temporary workspace support.
- **SAFE-04**: Add rollback or diff review workflow for file edits.
- **SAFE-05**: Add richer permission profiles around destructive actions, command allowlists, and per-workspace approval policy.

### Memory, Hooks, And Evaluation

- **MEM-01**: Add a JSON or SQLite memory store.
- **MEM-02**: Add memory extraction through `RuntimeObserver`.
- **MEM-03**: Add memory retrieval through `ContextSource`.
- **HOOK-01**: Add hook support through observers.
- **EVAL-01**: Add session replay and trace export.
- **EVAL-02**: Add evaluation fixtures for common coding-agent tasks.

## Out of Scope

Explicitly excluded from the current GSD-managed milestone.

| Feature | Reason |
|---------|--------|
| Full long-term memory implementation | Context source boundaries should land first. |
| Workspace sandboxing and worktree isolation | Planned as a later workspace safety milestone. |
| Multi-agent task decomposition | Long-term idea, not required for MCP integration. |
| Visual UI or TUI session viewer | Long-term idea, not needed for the current SDK/CLI milestone. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SESS-01 | Phase 1 | Complete |
| CTX-01 | Phase 2 | Pending |
| CTX-02 | Phase 2 | Pending |
| CTX-03 | Phase 3 | Pending |
| CTX-04 | Phase 3 | Pending |
| MCP-01 | Phase 4 | Pending |
| MCP-02 | Phase 5 | Pending |
| MCP-03 | Phase 6 | Pending |
| MCP-04 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-06-22*
*Last updated: 2026-06-22 after ingesting docs into GSD planning.*
