# CitrusButter Roadmap

This roadmap keeps CitrusButter lightweight while leaving clear extension paths
for future engineering work. Each phase should produce runnable code, tests, and
documentation.

## V1: Runtime Kernel

Goal: build the smallest useful coding harness with stable extension boundaries.

- Done: Python package and `citrus` CLI.
- Done: `AgentRuntime` loop.
- Done: Internal message, tool call, and tool result models.
- Done: Anthropic, OpenAI, DeepSeek, and Fake providers.
- Done: Project-local `.citrus/config.toml` with env and CLI overrides.
- Done: Local tools: read file, write file, search files, run shell.
- Done: Permission policy for reads, writes, and shell commands.
- Done: Lightweight context builder.
- Done: Structured session event stream.
- Done: In-memory and JSONL session stores.
- Done: No-op memory boundary.
- Done: `ToolSource` boundary for future MCP support.
- Done: Contract tests for providers, tools, permissions, context, sessions, and
  extension points.
- Gap: CLI currently uses in-memory sessions; JSONL persistence should be exposed
  through a CLI option or default `.citrus/sessions/` directory.

Manual smoke status:

- DeepSeek CLI call with configured project API key returned `citrus-ok`.

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
