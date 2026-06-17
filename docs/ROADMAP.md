# CitrusButter Roadmap

This roadmap keeps CitrusButter lightweight while leaving clear extension paths
for future engineering work. Each phase should produce runnable code, tests, and
documentation.

## V1: Runtime Kernel

Goal: build the smallest useful coding harness with stable extension boundaries.

- Python package and `citrus` CLI.
- `AgentRuntime` loop.
- Internal message, tool call, and tool result models.
- Anthropic, OpenAI, DeepSeek, and Fake providers.
- Local tools: read file, write file, search files, run shell.
- Permission policy for reads, writes, and shell commands.
- Lightweight context builder.
- Structured session event stream.
- No-op memory boundary.
- `ToolSource` boundary for future MCP support.
- Contract tests for providers, tools, permissions, context, sessions, and
  extension points.

## V2: External Tools And MCP

Goal: prove the tool system can import external capabilities without changing
the runtime loop.

- Implement `MCPToolSource`.
- Add MCP server configuration.
- Normalize MCP tools into CitrusButter `Tool` objects.
- Add contract tests showing MCP tools and local tools share the same execution
  path.

## V3: Workspace Safety

Goal: improve local execution safety and task isolation.

- Add workspace policy for allowed paths.
- Add safer shell execution profiles.
- Consider git worktree or temporary workspace support.
- Add rollback or diff review workflow for file edits.
- Expand permission tests around destructive actions.

## V4: Memory, Hooks, And Evaluation

Goal: make long-running project work observable, replayable, and learnable.

- Add JSON or SQLite memory store.
- Add memory extraction through `RuntimeObserver`.
- Add memory retrieval through `ContextSource`.
- Add hook support through observers.
- Add session replay and trace export.
- Add evaluation fixtures for common coding-agent tasks.

## Long-Term Ideas

- Multi-agent task decomposition.
- Richer repository indexing.
- Provider-specific optimization such as caching or reasoning controls.
- Web or TUI session viewer.
- Remote execution backends.

