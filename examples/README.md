# Examples

## `basic/server.py`

A runnable MCP server with 5 toy capabilities across unrelated domains
(weather, currency conversion, support tickets, order lookup, email) —
all exposed through the same 3 meta-tools.

```bash
uv run examples/basic/server.py
```

Point an MCP client at it and try `search_capabilities("send someone an email")`
or `search_capabilities("check order status")`.

## `benchmark/token_comparison.py`

A standalone script (no server, no MCP client needed) comparing the
approximate tool-definition token cost of a traditional one-tool-per-endpoint
server against mcp-lens's fixed 3 tools, as catalog size grows from 10 to
1,000 entries.

```bash
python examples/benchmark/token_comparison.py
```
