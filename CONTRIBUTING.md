# Contributing to mcp-lens

Thanks for considering a contribution. This project is intentionally small
in scope — see the "Non-goals" section of the [README](README.md) before
proposing a feature that adds auth, persistence, or a UI layer; those are
product decisions that belong in a project built on top of mcp-lens, not in
the pattern itself.

## Local setup

```bash
git clone https://github.com/helygp/mcp-lens.git
cd mcp-lens
uv sync --group dev
uv run pre-commit install   # optional, if you have pre-commit configured
```

## Running checks

```bash
uv run pytest          # tests
uv run ruff check       # lint
```

## Two kinds of changes

**Changes to the reference implementation** (`src/mcp_lens/`): open a PR
directly. Include a test for any behavior change. Keep `registry.py` free
of any MCP-specific dependency — that boundary is intentional.

**Changes to the contract itself** (`SPEC.md`): open an issue tagged
`spec` first, describing the problem with the current contract before
proposing the fix. Spec changes affect anyone implementing this pattern in
another language, not just this repository, so they get more scrutiny than
implementation changes.

## Reporting bugs

Open an issue with:
- What you expected `search_capabilities` / `get_capability_schema` /
  `execute_capability` to do
- What actually happened
- A minimal reproduction (a few `Capability` registrations is usually
  enough — you shouldn't need your real catalog to reproduce most bugs)

## Code style

- Type hints on public functions.
- No dependency added to `mcp_lens.registry` beyond the standard library.
  Anything MCP-specific belongs in `mcp_lens.server` or a new adapter
  module, not in the registry.
