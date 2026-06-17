# ADR 0002: Keep Memory Separate From Context And Sessions

## Status

Accepted for V1 planning.

## Context

Future versions of CitrusButter may support project memory, user preferences,
architecture decisions, common commands, and lessons learned across tasks.

Memory can easily become tangled with context assembly and session logging. If
that happens, adding long-term memory later would require modifying the runtime
loop, context builder, and storage code at the same time.

## Decision

CitrusButter will treat session, context, and memory as separate concepts:

- `SessionStore` records what happened during a task.
- `ContextBuilder` builds the temporary model input for the current turn.
- `MemoryService` manages durable facts that may be useful in future tasks.

V1 will include memory interfaces and a no-op implementation, but it will not
implement sophisticated long-term memory.

Future memory should attach through two extension points:

- `MemoryContextSource` retrieves relevant memory before a task.
- `MemoryObserver` watches runtime events and proposes memory updates.

## Consequences

- V1 remains lightweight.
- Future memory stores can be JSON, SQLite, vector-based, remote, or MCP-backed.
- Memory can be tested independently from context assembly and session storage.
- The runtime should not contain memory-specific branching beyond calling the
  standard context and observer interfaces.

