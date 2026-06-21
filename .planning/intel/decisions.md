# Synthesized Decisions

## ADR 0001: Use A Runtime Kernel Architecture

source: docs/ADR/0001-runtime-kernel.md
status: locked
scope: AgentRuntime, ModelProvider, ToolRegistry, PermissionPolicy, ContextBuilder, SessionStore, MemoryService, RuntimeObserver, CLI

CitrusButter uses `AgentRuntime` as a small runtime kernel. The runtime owns the agent loop and depends on narrow replaceable interfaces for providers, tools, permissions, context, sessions, memory, and observers. The CLI is a client of the SDK, not the owner of business logic.

## ADR 0002: Keep Memory Separate From Context And Sessions

source: docs/ADR/0002-memory-boundary.md
status: locked
scope: SessionStore, ContextBuilder, MemoryService, MemoryContextSource, MemoryObserver, AgentRuntime

CitrusButter treats session history, active context assembly, and durable memory as separate concepts. Future memory should attach through `MemoryContextSource` and `MemoryObserver` instead of adding memory-specific branching to the runtime loop.

## ADR 0003: Represent Future MCP Support As A ToolSource

source: docs/ADR/0003-toolsource-for-mcp.md
status: locked
scope: ToolSource, MCPToolSource, ToolRegistry, Tool, permissions, AgentRuntime

CitrusButter represents future MCP support through the `ToolSource` boundary. MCP tools should be imported and exposed as standard CitrusButter `Tool` objects so local and external tools share one execution and permission path.
