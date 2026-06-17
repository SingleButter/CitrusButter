# ADR 0003: Represent Future MCP Support As A ToolSource

## Status

Accepted for V1 planning.

## Context

MCP is an important future extension path, but implementing a full MCP client in
V1 would make the first version larger and risk distracting from the runtime
kernel.

The system still needs a clear path for external tools so that MCP can be added
without redesigning local tool execution.

## Decision

CitrusButter will define a lightweight `ToolSource` interface:

```python
class ToolSource(Protocol):
    def list_tools(self) -> list[Tool]:
        ...
```

V1 will use local tools directly through `ToolRegistry`. Future MCP support will
be implemented as `MCPToolSource`, which imports MCP tools and exposes them as
standard CitrusButter `Tool` objects.

## Consequences

- Local tools and future MCP tools share one execution path.
- Permissions can apply consistently to all tools.
- The runtime does not need MCP-specific logic.
- V1 can document and test the extension boundary without implementing the full
  MCP protocol immediately.

