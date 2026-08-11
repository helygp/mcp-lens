"""FastMCP adapter — wraps a CapabilityRegistry as an MCP server that exposes
exactly 3 tools, no matter how many capabilities are registered behind it.

This is a thin adapter on purpose. All the actual logic (search ranking,
schema lookup, execution, error handling) lives in `mcp_lens.registry` and
has no MCP dependency. Swap this file out if you're on the low-level
`mcp` SDK, a different language, or a custom transport — the registry
underneath does not need to change.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from .registry import CapabilityRegistry


def build_server(registry: CapabilityRegistry, name: str = "mcp-lens") -> FastMCP:
    """Build a ready-to-run FastMCP server backed by `registry`.

    Usage:
        registry = CapabilityRegistry()
        registry.register_many([...])
        mcp = build_server(registry)
        mcp.run()
    """
    mcp = FastMCP(name)

    @mcp.tool()
    def search_capabilities(query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the capability catalog by keyword or natural language.

        Always call this first. Capability keys are not guessable and are
        not listed anywhere else — this is the only way to discover them.
        Returns short summaries; call get_capability_schema() on a result
        before calling execute_capability().
        """
        return registry.search_capabilities(query, limit)

    @mcp.tool()
    def get_capability_schema(key: str) -> dict[str, Any]:
        """Get the input schema for a capability key returned by search_capabilities()."""
        return registry.get_capability_schema(key)

    @mcp.tool()
    async def execute_capability(key: str, input: dict[str, Any] | None = None) -> Any:
        """Execute a capability by key, with input matching its schema."""
        return await registry.execute_capability(key, input)

    return mcp
