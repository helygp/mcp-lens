# mcp-lens

**Progressive disclosure for large MCP tool catalogs.**

[![CI](https://github.com/helygp/mcp-lens/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Spec](https://img.shields.io/badge/spec-SPEC.md-informational)](SPEC.md)
[![Status](https://img.shields.io/badge/status-alpha-orange)](CHANGELOG.md)

**[Quick Start](#quick-start)** · **[Spec](SPEC.md)** · **[Examples](examples/)** · **[Contributing](CONTRIBUTING.md)**

Most MCP servers expose one tool per endpoint. That works until your catalog
grows — 20 endpoints becomes 20 tool definitions loaded into every context
window, 200 becomes 200, and the model starts guessing wrong between
similarly-named tools long before you get there.

mcp-lens is a small, dependency-light pattern (and a Python reference
implementation) for the alternative: expose exactly **3 stable meta-tools** —
`search_capabilities`, `get_capability_schema`, `execute_capability` — no
matter how many capabilities sit behind them. The tool-definition cost the
model pays is O(1) in catalog size; only what `search_capabilities` actually
returns grows with your catalog.

```python
from mcp_lens import Capability, CapabilityRegistry, build_server

registry = CapabilityRegistry()
registry.register(
    Capability(
        key="billing.create_invoice",
        description="Create an invoice for a customer",
        input_schema={
            "type": "object",
            "properties": {"customer_id": {"type": "string"}, "amount": {"type": "number"}},
            "required": ["customer_id", "amount"],
        },
        executor=lambda customer_id, amount: {"invoice_id": "INV-001", "amount": amount},
    )
)
# ...register 5, 50, or 5,000 more capabilities the same way...

mcp = build_server(registry, name="my-server")
mcp.run()
```

Whether `registry` holds 1 capability or 5,000, the MCP client always sees
the same 3 tools.

## Why this, specifically

- **The registry has no MCP dependency.** `mcp_lens.registry` is plain
  Python — testable, reusable, and swappable behind any transport. The
  FastMCP adapter in `mcp_lens.server` is a thin, optional layer on top.
- **Search is pluggable.** The default matcher is keyword substring
  matching, fine for demos. Pass your own `search_fn` to
  `CapabilityRegistry` for Postgres full-text, embeddings, or whatever
  search backend you already run — the 3-tool contract doesn't change.
- **It's a spec, not just a library.** [`SPEC.md`](SPEC.md) defines the
  contract (tool names, schemas, semantics) independently of this
  implementation, so it can be implemented in other languages and still
  interoperate conceptually.
- **Validated with real traffic**, not just a thought experiment — this
  pattern (search → schema → execute) has been running in production MCP
  servers before this repository existed; this is the extracted, product-agnostic version of that mechanism.

## Installation

Add mcp-lens to a new or existing Python project with
[uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
uv add mcp-lens
```

Or with pip:

```bash
pip install mcp-lens
```

**Installing from source — track `main`:**

```bash
uv add "mcp-lens @ git+https://github.com/helygp/mcp-lens.git@main"
```

## Quick Start

### 1. Define your capabilities

A `Capability` is a key, a description, a JSON Schema for its input, and a
callable (sync or async) that runs it:

```python
from mcp_lens import Capability

def get_weather(city: str) -> str:
    return f"Sunny in {city}"

weather = Capability(
    key="weather.get_weather",
    description="Get current weather for a city",
    input_schema={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
    executor=get_weather,
    tags=("weather", "forecast"),
)
```

### 2. Register them

```python
from mcp_lens import CapabilityRegistry

registry = CapabilityRegistry()
registry.register(weather)
# or: registry.register_many([weather, other_capability, ...])
```

### 3. Serve them

```python
from mcp_lens import build_server

mcp = build_server(registry, name="my-server")

if __name__ == "__main__":
    mcp.run()
```

Run the checked-in example instead of writing your own from scratch:

```bash
uv run examples/basic/server.py
```

See [`examples/README.md`](examples/) for the full walkthrough, including
the token-cost comparison in `examples/benchmark/`.

## Learn more

- **[SPEC.md](SPEC.md)** — the formal contract: tool names, schemas,
  semantics, and what's deliberately left out of scope (auth, persistence,
  discovery UI — those are yours to build).
- **[examples/](examples/)** — a runnable 5-capability example server and a
  before/after token-cost comparison as the catalog grows.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — how to propose changes, including
  changes to the spec itself.

## Related work

This pattern isn't new — [Twenty CRM](https://github.com/twentyhq/twenty) uses
a similar fixed-meta-tool approach for its MCP server, and "don't load every
tool definition up front" is an increasingly common idea across the MCP
ecosystem as catalogs grow. What mcp-lens adds is not the idea itself but:
a formal, implementation-agnostic contract for it (`SPEC.md`), a tested
reference implementation with the MCP-specific parts cleanly separated from
the reusable core, and measured numbers for the tradeoff instead of just the
claim. If you know of other implementations of this pattern, a PR adding
them here is welcome.

## Non-goals

mcp-lens is deliberately narrow. It does **not** provide: authentication,
capability persistence/storage, an approval or review UI, or AI-assisted
onboarding of new capabilities. Those are real, useful things to build on
top of this — but they're product decisions, not part of the protocol
pattern this repo exists to document and implement.

## Contributing

```bash
git clone https://github.com/helygp/mcp-lens.git
cd mcp-lens
uv sync --group dev
uv run pytest
uv run ruff check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Citation

If mcp-lens or the pattern in `SPEC.md` is useful in your work, you can cite
the repository:

```bibtex
@software{mcp_lens,
  title  = {mcp-lens: Progressive disclosure for large MCP tool catalogs},
  author = {Pasqual, Hely},
  year   = {2026},
  url    = {https://github.com/helygp/mcp-lens}
}
```

## License

Apache 2.0. See [LICENSE](LICENSE).
