# Synthesized Requirements

## Current Milestone Requirements

### Session Persistence

- **SESS-01**: The CLI exposes JSONL session persistence through an option or default `.citrus/sessions/` directory.
  source: docs/ROADMAP.md, docs/V1_ARCHITECTURE.md

### Context Sources And Compaction

- **CTX-01**: CitrusButter provides a `ContextSource` extension boundary for repo summaries, project rules, selected memory notes, and future contextual inputs.
  source: docs/ROADMAP.md, docs/V2_CONTEXT_ARCHITECTURE.md, docs/design-thinking/context-builder-and-compactor.md
- **CTX-02**: `ContextBuilder` can retrieve selected context source output and place it into active messages without changing `AgentRuntime`.
  source: docs/V2_CONTEXT_ARCHITECTURE.md, docs/design-thinking/context-builder-and-compactor.md
- **CTX-03**: Context compaction can optionally use provider-aware token budgeting while preserving valid assistant tool-call/tool-result sequences.
  source: docs/ROADMAP.md, docs/V2_CONTEXT_ARCHITECTURE.md
- **CTX-04**: Context compaction can optionally use LLM summary compaction or a layered compaction pipeline behind the same compactor boundary.
  source: docs/ROADMAP.md, docs/design-thinking/context-builder-and-compactor.md

### External Tools And MCP

- **MCP-01**: CitrusButter implements `MCPToolSource` without moving MCP-specific logic into `AgentRuntime`.
  source: docs/ROADMAP.md, docs/ADR/0003-toolsource-for-mcp.md
- **MCP-02**: CitrusButter supports MCP server configuration using the existing configuration boundary.
  source: docs/ROADMAP.md, docs/ADR/0003-toolsource-for-mcp.md
- **MCP-03**: MCP tools are normalized into standard CitrusButter `Tool` objects.
  source: docs/ROADMAP.md, docs/ADR/0003-toolsource-for-mcp.md
- **MCP-04**: Contract tests prove MCP tools and local tools share the same execution and permission path.
  source: docs/ROADMAP.md, docs/ADR/0003-toolsource-for-mcp.md

## Deferred Requirements

### Workspace Safety

- **SAFE-01**: Add workspace policy for allowed paths.
  source: docs/ROADMAP.md
- **SAFE-02**: Add safer shell execution profiles.
  source: docs/ROADMAP.md
- **SAFE-03**: Consider git worktree or temporary workspace support.
  source: docs/ROADMAP.md
- **SAFE-04**: Add rollback or diff review workflow for file edits.
  source: docs/ROADMAP.md
- **SAFE-05**: Add richer permission profiles around destructive actions, command allowlists, and per-workspace approval policy.
  source: docs/ROADMAP.md

### Memory, Hooks, And Evaluation

- **MEM-01**: Add a JSON or SQLite memory store.
  source: docs/ROADMAP.md
- **MEM-02**: Add memory extraction through `RuntimeObserver`.
  source: docs/ROADMAP.md, docs/ADR/0002-memory-boundary.md
- **MEM-03**: Add memory retrieval through `ContextSource`.
  source: docs/ROADMAP.md, docs/ADR/0002-memory-boundary.md
- **HOOK-01**: Add hook support through observers.
  source: docs/ROADMAP.md
- **EVAL-01**: Add session replay and trace export.
  source: docs/ROADMAP.md
- **EVAL-02**: Add evaluation fixtures for common coding-agent tasks.
  source: docs/ROADMAP.md
