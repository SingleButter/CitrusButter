# Synthesized Context

## Project Summary

source: docs/V1_ARCHITECTURE.md, docs/ROADMAP.md

CitrusButter is a Python SDK and CLI coding-agent harness. It is intentionally small, modular, and testable, with extension points for providers, tools, permissions, context, sessions, memory, observers, MCP, sandboxing, hooks, and evaluation.

## Current Implementation State

source: docs/ROADMAP.md, docs/V1_ARCHITECTURE.md, docs/V2_CONTEXT_ARCHITECTURE.md

V1 is implemented: the package, CLI, runtime loop, providers, local tools, permission policy, interactive approval, chat, context builder, session stores, no-op memory boundary, `ToolSource` boundary, and contract tests exist. V2 context and deterministic compaction are also implemented at the core level. Remaining V2 work is focused on `ContextSource` and optional provider-aware or LLM-backed compaction. V3 focuses on MCP integration through `ToolSource`.

## Existing Product Roadmap

source: docs/ROADMAP.md

The product roadmap orders future work as V2 context extensions, V3 external tools and MCP, V4 workspace safety, and V5 memory, hooks, and evaluation. Long-term ideas include multi-agent task decomposition, richer repository indexing, provider-specific optimization, web or TUI session viewing, and remote execution backends.

## Context Design Rationale

source: docs/design-thinking/context-builder-and-compactor.md

The active context model distinguishes active messages from session history and durable memory. Active context may be compacted; session history should remain an append-only audit trail; memory is a selected set of durable facts. Future OpenCode-style auto compact, NanoBot-style memory/context retrieval, and learn-claude-code-style layered compaction should fit behind `ContextBuilder`, `ContextSource`, and `ContextCompactor` boundaries.
