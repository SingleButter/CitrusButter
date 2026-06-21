# CitrusButter

## What This Is

CitrusButter is a Python SDK and CLI coding-agent harness for building local coding-agent workflows. It provides a small runtime kernel with replaceable providers, tools, permissions, context, sessions, memory, and observer boundaries, while keeping the CLI as a client of the SDK.

The existing codebase has shipped the V1 runtime kernel and the core V2 context compaction work. Current development continues from that brownfield state toward session persistence, context sources, advanced compaction, and MCP tool integration.

## Core Value

Keep `AgentRuntime` as the stable owner of the agent loop while every major capability remains replaceable at a narrow boundary.

## Requirements

### Validated

- V1 runtime kernel is implemented with CLI commands, provider adapters, local tools, permission checks, context assembly, session stores, and contract tests.
- V2 deterministic context compaction is implemented with pair-safe handling of assistant tool calls and tool results.
- The `ToolSource` boundary exists for future MCP integration.
- The memory boundary exists as interfaces and a no-op implementation, separate from context and session history.

### Active

- [ ] Expose JSONL session persistence through the CLI.
- [ ] Add `ContextSource` support for repo summaries, project rules, and selected memory notes.
- [ ] Add optional provider-aware token budgeting or LLM summary compaction behind the context boundary.
- [ ] Implement MCP tool ingestion through `MCPToolSource`.
- [ ] Prove local tools and MCP tools share the same execution and permission path.

### Out of Scope

- Full long-term memory implementation - deferred until after context sources and MCP are stable.
- Workspace sandboxing and worktree isolation - deferred to the workspace safety milestone.
- Multi-agent orchestration - long-term idea, not part of the current milestone.
- Visual UI or TUI session viewer - long-term idea, not part of the current milestone.

## Context

CitrusButter is already a working Python 3.11+ package under `src/citrus/` with tests in `tests/`. The repository also contains architecture docs and ADRs under `docs/`.

The product roadmap documents V1 as complete and V2 core context work as complete. The next useful development boundary is to finish the remaining V2 extension hooks, then build V3 external tools and MCP without changing the core runtime ownership model.

## Constraints

- **Architecture**: `AgentRuntime` owns the loop - providers, tools, permissions, context, sessions, memory, and observers remain replaceable dependencies.
- **Provider boundary**: Provider-specific API formats must stay inside provider adapters.
- **Tool boundary**: Local tools and future MCP tools must expose standard CitrusButter `Tool` objects.
- **Context boundary**: Active context, session history, and durable memory must remain separate.
- **Provider compatibility**: Context compaction must preserve valid assistant tool-call/tool-result sequences.
- **Verification**: Changes should pass pytest, ruff, mypy, and relevant fake-provider or provider smoke checks.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use `AgentRuntime` as the runtime kernel | Keeps the agent loop stable while dependencies evolve independently | Good |
| Keep memory separate from context and sessions | Prevents durable memory from tangling with active context or audit history | Good |
| Represent future MCP support as `ToolSource` | Lets MCP tools share the same execution and permission path as local tools | Pending |

---
*Last updated: 2026-06-22 after ingesting docs into GSD planning.*
