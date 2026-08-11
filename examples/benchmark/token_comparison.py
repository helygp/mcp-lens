"""Compare context cost: one MCP tool per endpoint ("traditional") vs the
fixed 3 meta-tools of mcp-lens, as the capability catalog grows.

This uses a simple chars/4 approximation for tokens — no tokenizer
dependency, good enough to see the shape of the curve. Swap in `tiktoken`
if you want exact counts for a specific model.

Run it:
    python examples/benchmark/token_comparison.py
"""

from __future__ import annotations

import json


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def traditional_tool_schema(i: int) -> dict:
    """Stand-in for what a hand-written MCP tool definition looks like —
    representative size, not a specific real API."""
    return {
        "name": f"do_operation_{i}",
        "description": f"Perform operation {i} against the underlying system, "
        f"with validation and error handling for common failure modes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_id": {"type": "string", "description": "Identifier of the target resource"},
                "options": {"type": "object", "description": "Optional parameters for this operation"},
                "dry_run": {"type": "boolean", "description": "If true, validate without executing"},
            },
            "required": ["resource_id"],
        },
    }


MCP_LENS_TOOLS = [
    {
        "name": "search_capabilities",
        "description": "Search the capability catalog by keyword or natural language.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_capability_schema",
        "description": "Get the input schema for a capability key returned by search_capabilities.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    },
    {
        "name": "execute_capability",
        "description": "Execute a capability by key, with input matching its schema.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}, "input": {"type": "object"}},
            "required": ["key"],
        },
    },
]


def main() -> None:
    fixed_cost = approx_tokens(json.dumps(MCP_LENS_TOOLS))
    print(f"{'catalog size':>12} | {'traditional (~tokens)':>22} | {'mcp-lens (~tokens)':>18}")
    print("-" * 58)
    for n in (10, 50, 100, 250, 500, 1000):
        traditional_cost = sum(approx_tokens(json.dumps(traditional_tool_schema(i))) for i in range(n))
        print(f"{n:>12} | {traditional_cost:>22} | {fixed_cost:>18}")
    print()
    print("mcp-lens's tool-definition cost is O(1) in catalog size — it only")
    print("grows with what search_capabilities() actually returns per call,")
    print("not with everything that exists in the catalog.")


if __name__ == "__main__":
    main()
