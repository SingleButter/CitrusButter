# ADR 0001: Use A Runtime Kernel Architecture

## Status

Accepted for V1 planning.

## Context

CitrusButter needs to be a real engineering project, not a one-off CLI demo.
Future functionality may include new model providers, tools, permission modes,
memory systems, MCP integration, tracing, hooks, and evaluation.

If the agent loop directly knows about every feature, each extension will require
editing the same central code path and the project will become fragile.

## Decision

CitrusButter will use `AgentRuntime` as a small runtime kernel. The runtime owns
the agent loop, but depends on narrow interfaces:

- `ModelProvider`
- `ToolRegistry`
- `PermissionPolicy`
- `ContextBuilder`
- `SessionStore`
- `MemoryService`
- `RuntimeObserver`

The CLI is a client of the SDK, not the owner of business logic.

## Consequences

- New providers, tools, memory backends, observers, and context sources should
  be added without modifying the core runtime loop.
- The runtime must use CitrusButter internal data models instead of
  provider-specific API objects.
- Contract tests are required to prove extension boundaries remain stable.
- V1 may look slightly more structured than a quick script, but the structure is
  intentionally limited to extension points with clear future value.

