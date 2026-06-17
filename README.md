# CitrusButter

CitrusButter is a Python SDK + CLI coding agent harness. It is designed as a
small runtime kernel with clear extension points for model providers, tools,
permissions, context, memory, sessions, and future MCP support.

The first version focuses on a lightweight foundation:

- `citrus` CLI entry point
- Python SDK package under `citrus`
- Runtime-kernel architecture
- Modern `uv` project setup
- Test-first implementation workflow

See [docs/V1_ARCHITECTURE.md](docs/V1_ARCHITECTURE.md) for the current V1
architecture plan.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src
```

## CLI

```bash
citrus --help
citrus run "inspect this project"
citrus providers
citrus config
```

