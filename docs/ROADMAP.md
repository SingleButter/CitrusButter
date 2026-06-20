# CitrusButter Roadmap

This roadmap keeps CitrusButter lightweight while leaving clear extension paths
for future engineering work. Each phase should produce runnable code, tests, and
documentation.

## V1: Runtime Kernel

Goal: build the smallest useful coding harness with stable extension boundaries.

- Done: Python package and `citrus` CLI with `run` and process-local `chat` modes.
- Done: `AgentRuntime` loop.
- Done: Internal message, tool call, and tool result models.
- Done: Anthropic, OpenAI, DeepSeek, and Fake providers.
- Done: Project-local `.citrus/config.toml` with env and CLI overrides.
- Done: Local tools: read file, write file, search files, run shell.
- Done: Permission policy for reads, writes, and shell commands.
- Done: Runtime `PermissionApprover` callback and CLI approval prompt for
  `ask` decisions.
- Done: Interactive `citrus chat` command with shared in-process model context
  and `exit` / `quit` / `:q` shutdown commands.
- Done: Lightweight context builder.
- Done: Structured session event stream.
- Done: In-memory and JSONL session stores.
- Done: No-op memory boundary.
- Done: `ToolSource` boundary for future MCP support.
- Done: Contract tests for providers, tools, permissions, CLI approval prompts,
  interactive chat context, sessions, and extension points.
- Gap: CLI currently uses in-memory sessions; JSONL persistence should be exposed
  through a CLI option or default `.citrus/sessions/` directory.

Manual smoke status:

- DeepSeek CLI call with configured project API key returned `citrus-ok`.

## V2: Context Management And Compaction

Goal: make multi-turn chat context bounded and extensible without changing the
agent loop ownership model.

- Done: `ContextBuilder` can assemble prior active messages plus the current
  user task for each runtime request.
- Done: `ContextCompactor` runs before every provider call and keeps active
  messages deterministic, pair-safe, and bounded.
- Done: Old large tool results can be compacted while preserving
  `tool_call_id`.
- Done: Middle history can be snipped without splitting assistant tool calls
  from matching tool results.
- Done: Design notes explain how the interface can later support OpenCode-style
  auto compact, NanoBot-style memory/context, and learn-claude-code-style
  multi-layer compaction.
- Next: Add `ContextSource` for repo summaries and selected memory notes.
- Next: Add optional provider-aware token budgeting or LLM summary compaction.

## V3: External Tools And MCP

Goal: prove the tool system can import external capabilities without changing
the runtime loop.

- Implement `MCPToolSource`.
- Add MCP server configuration.
- Normalize MCP tools into CitrusButter `Tool` objects.
- Add contract tests showing MCP tools and local tools share the same execution
  path.

## V4: Workspace Safety

Goal: improve local execution safety and task isolation.

- Add workspace policy for allowed paths.
- Add safer shell execution profiles.
- Consider git worktree or temporary workspace support.
- Add rollback or diff review workflow for file edits.
- Add richer permission profiles around destructive actions, command allowlists,
  and per-workspace approval policy.

## V5: Memory, Hooks, And Evaluation

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
