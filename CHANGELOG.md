# Changelog

## 0.1.1

Fixes README install instructions that still referenced the old PyPI
package name after the 0.1.0 → mcp-lens-py rename. No code changes.

## 0.1.0 — unreleased

Initial extraction of the progressive-disclosure pattern (previously
implemented ad hoc in two internal production MCP servers) into a
standalone, product-agnostic spec and Python reference implementation.

- `CapabilityRegistry` — framework-agnostic core (`src/mcp_lens/registry.py`)
- `build_server` — FastMCP adapter (`src/mcp_lens/server.py`)
- `SPEC.md` v0.1 — draft contract for the 3 meta-tools
- Basic example server and token-cost benchmark under `examples/`
