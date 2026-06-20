# Repository Guidelines

This guide applies only to CitrusButter, not to global Codex settings.

## Project Structure & Module Organization
CitrusButter is a Python SDK and CLI coding-agent harness. Source code is in
`src/citrus/`, with packages for CLI, config, context, memory, permissions,
providers, runtime, sessions, and tools. Tools are in
`src/citrus/tools/local/`; tests in `tests/`; docs and ADRs in `docs/`; the
static site in `site/`.

## Build, Test, and Development Commands
- `uv sync --extra dev` installs development tools.
- `uv sync --extra dev --extra providers` installs provider SDKs.
- `uv run citrus --help` checks the CLI entry point.
- `uv run citrus run "say hello" --provider fake --fake-response hello` runs a smoke test.
- `uv run citrus chat --provider fake --fake-response hello` starts chat.
- `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` verify work.

## Coding Style & Naming Conventions
Use Python 3.11+, four-space indentation, type hints, and Pydantic models. Keep
modules boundary-oriented: runtime owns the loop; providers, tools,
permissions, context, sessions, memory, and observers stay replaceable. 


## Agent-Specific Architecture Rules
When discussing architecture or implementation design, first map the topic to a
known harness area: agent loop, tools, permissions, context compaction, memory,
hooks, MCP, worktree isolation, or task/subagent systems.

Use `shareAI-lab/learn-claude-code` as the primary reference for early/simple
implementations, matching the relevant chapter when possible. Use HelloAgent,
`earendil-works/pi`, Claude Code, `anomalyco/opencode`, and `HKUDS/NanoBot` as
secondary comparisons.

Extract principles, not code. Do not copy APIs, prompts, licenses, or
implementation details blindly. Keep CitrusButter's core rule intact:
`AgentRuntime` owns the loop; dependencies remain replaceable. If a reference
cannot be verified or mapped, say so and continue from local constraints.

## Security & Configuration Tips
Do not commit API keys. Project-local config belongs in `.citrus/config.toml`,
which is ignored by git.
