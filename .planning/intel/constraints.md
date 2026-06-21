# Synthesized Constraints

## Runtime Ownership

source: docs/ADR/0001-runtime-kernel.md, docs/V1_ARCHITECTURE.md
type: architecture

`AgentRuntime` owns the loop. Providers, tools, permissions, context, sessions, memory, observers, and future MCP integrations must remain replaceable dependencies.

## Provider Boundary

source: docs/V1_ARCHITECTURE.md
type: adapter-contract

Provider-specific API formats must be translated at provider adapter boundaries. The runtime uses CitrusButter internal message and tool-result models.

## Tool And Permission Path

source: docs/ADR/0003-toolsource-for-mcp.md
type: extension-contract

Local tools and future MCP tools must share the standard `Tool` execution path so permissions apply consistently.

## Context Boundary

source: docs/ADR/0002-memory-boundary.md, docs/V2_CONTEXT_ARCHITECTURE.md, docs/design-thinking/context-builder-and-compactor.md
type: architecture

`ContextBuilder` assembles active context, `ContextCompactor` prepares active messages before provider calls, `SessionStore` records full history, and `MemoryService` manages durable facts.

## Tool-Call Pair Safety

source: docs/V2_CONTEXT_ARCHITECTURE.md, docs/design-thinking/context-builder-and-compactor.md
type: provider-compatibility

Compaction must not split assistant tool calls from matching tool results. Pair-safe segments are required for OpenAI-compatible providers such as OpenAI and DeepSeek.

## Verification Baseline

source: docs/ROADMAP.md, docs/V1_ARCHITECTURE.md
type: quality

Each phase should produce runnable code, tests, and documentation. Verification should include pytest, ruff, mypy, and relevant fake-provider or real-provider smoke checks.
