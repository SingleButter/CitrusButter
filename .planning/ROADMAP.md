# Roadmap: CitrusButter

## Overview

This GSD roadmap starts from the existing brownfield state: the V1 runtime kernel and core V2 context compaction are already implemented. The current milestone finishes the remaining V2 extension hooks, then delivers V3 external tools and MCP through the existing `ToolSource` boundary.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: CLI Session Persistence** - Expose JSONL session persistence from the CLI.
- [ ] **Phase 2: ContextSource Boundary** - Add retrievable context sources without changing the runtime loop.
- [ ] **Phase 3: Advanced Context Compaction** - Add optional provider-aware budgeting and summary compaction behind the compactor boundary.
- [ ] **Phase 4: MCP ToolSource Foundation** - Implement MCP tools as a `ToolSource`.
- [ ] **Phase 5: MCP Configuration** - Add MCP server configuration through existing config paths.
- [ ] **Phase 6: MCP Normalization And Contracts** - Normalize MCP tools into `Tool` objects and prove shared execution behavior.

## Phase Details

### Phase 1: CLI Session Persistence
**Goal**: CLI users can opt into durable JSONL session history without affecting the runtime loop.
**Depends on**: Nothing (first phase)
**Requirements**: SESS-01
**Success Criteria** (what must be TRUE):
  1. User can run `citrus` with a CLI option or default path that writes JSONL session events.
  2. User can inspect persisted session files under the configured location.
  3. Existing in-memory session behavior still works for tests and lightweight runs.
  4. pytest, ruff, and mypy pass after the CLI persistence change.
**Plans**: TBD

### Phase 2: ContextSource Boundary
**Goal**: Context retrieval becomes an additive dependency of `ContextBuilder` rather than runtime logic.
**Depends on**: Phase 1
**Requirements**: CTX-01, CTX-02
**Success Criteria** (what must be TRUE):
  1. Developer can implement a `ContextSource` that returns contextual notes for a task.
  2. `ContextBuilder` can include source output in active messages before the user task.
  3. `AgentRuntime` remains unaware of concrete context source implementations.
  4. Tests cover source ordering, empty sources, and source failures or omissions.
**Plans**: TBD

### Phase 3: Advanced Context Compaction
**Goal**: Context compaction can grow beyond deterministic character limits while preserving the same public boundary.
**Depends on**: Phase 2
**Requirements**: CTX-03, CTX-04
**Success Criteria** (what must be TRUE):
  1. Developer can enable provider-aware budgeting without changing runtime loop code.
  2. Developer can add or select an LLM summary compactor behind the `ContextCompactor` interface.
  3. Pair-safe assistant tool-call/tool-result handling remains covered by tests.
  4. Deterministic compaction remains the default and continues to pass existing tests.
**Plans**: TBD

### Phase 4: MCP ToolSource Foundation
**Goal**: MCP integration starts as a tool source, not as runtime-specific MCP logic.
**Depends on**: Phase 3
**Requirements**: MCP-01
**Success Criteria** (what must be TRUE):
  1. Developer can instantiate an `MCPToolSource` through the tool source boundary.
  2. The new source can list external tool definitions in a CitrusButter-compatible shape.
  3. MCP-specific protocol code stays outside `AgentRuntime`.
  4. Unit tests prove the boundary can be exercised with fake MCP data.
**Plans**: TBD

### Phase 5: MCP Configuration
**Goal**: Users can configure MCP servers through the existing configuration system.
**Depends on**: Phase 4
**Requirements**: MCP-02
**Success Criteria** (what must be TRUE):
  1. User can declare MCP server configuration in the same config-loading hierarchy as providers and models.
  2. Invalid MCP configuration produces clear validation errors.
  3. Existing `.citrus/config.toml`, `CITRUS_CONFIG`, environment, and CLI precedence rules remain intact.
  4. Tests cover config parsing and precedence behavior for MCP settings.
**Plans**: TBD

### Phase 6: MCP Normalization And Contracts
**Goal**: MCP tools behave like local CitrusButter tools from the runtime and permission system's point of view.
**Depends on**: Phase 5
**Requirements**: MCP-03, MCP-04
**Success Criteria** (what must be TRUE):
  1. MCP tools are normalized into standard `Tool` objects with schemas and `ToolResult` output.
  2. Runtime tool execution does not branch on local-vs-MCP tool origin.
  3. Permission policy applies consistently to local and MCP tools.
  4. Contract tests prove MCP tools and local tools share the same execution path.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. CLI Session Persistence | 0/TBD | Not started | - |
| 2. ContextSource Boundary | 0/TBD | Not started | - |
| 3. Advanced Context Compaction | 0/TBD | Not started | - |
| 4. MCP ToolSource Foundation | 0/TBD | Not started | - |
| 5. MCP Configuration | 0/TBD | Not started | - |
| 6. MCP Normalization And Contracts | 0/TBD | Not started | - |
