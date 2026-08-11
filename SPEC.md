# mcp-lens Spec v0.1

Status: Draft. Implementation-agnostic — this document defines a contract,
not a Python API. `src/mcp_lens/` is one implementation of it.

## 1. Motivation

An MCP server that exposes one tool per underlying operation scales its
context cost linearly with catalog size: every tool's name, description,
and JSON Schema is loaded into the model's context on every turn, whether
or not that tool is used. Past a few dozen tools this becomes:

- **Expensive** — tool definitions compete with the rest of the
  conversation for context budget.
- **Error-prone** — the model has to disambiguate between many
  similarly-named or similarly-scoped tools before it ever gets to
  execute anything.

This spec defines a fixed, 3-tool interface that keeps the model's
tool-definition cost constant (O(1) in catalog size) regardless of how many
capabilities exist behind it, by moving discovery into a first-class tool
call instead of the tool list itself.

## 2. Terminology

- **Capability**: one unit of functionality a system exposes — roughly
  analogous to what a single MCP tool would represent in the traditional
  one-tool-per-endpoint model.
- **Catalog**: the full set of capabilities a given server has registered,
  which may be arbitrarily large.
- **Key**: a globally unique, stable string identifying one capability
  (e.g. `billing.create_invoice`). Keys are implementation details — they
  are not guaranteed to be human-guessable and MUST be discovered via
  `search_capabilities`, not assumed.

## 3. The three operations

An implementation of this spec exposes exactly three tools. Names below are
the reference names used in `src/mcp_lens/`; implementations MAY use
different literal tool names as long as the three-operation shape and
semantics are preserved, but SHOULD prefer these names for interoperability
of expectations across servers.

### 3.1 `search_capabilities`

**Purpose:** discover candidate capabilities relevant to a query.

| | |
|---|---|
| Input | `query: string` (required), `limit: integer` (optional, default implementation-defined, e.g. 10) |
| Output | list of summaries: `{ key, description, tags? }` |

Rules:
- MUST NOT return full input schemas — summaries only. Schemas are fetched
  separately (3.2) so that search results stay cheap even when a matched
  capability has a large schema.
- An empty or whitespace-only query MAY return an empty list rather than
  the entire catalog — returning the entire catalog on an empty query
  defeats the purpose of this operation once the catalog is large.
- Matching strategy (substring, full-text, embeddings, hybrid) is
  intentionally unspecified. Any strategy that returns relevant keys
  satisfies this spec.

### 3.2 `get_capability_schema`

**Purpose:** fetch the exact input contract for one capability, by key.

| | |
|---|---|
| Input | `key: string` (required) |
| Output | `{ key, description, input_schema }` where `input_schema` is a JSON Schema object |

Rules:
- MUST fail with a clear, catchable error for unknown keys (not a silent
  empty result) — see §5.
- Callers SHOULD call this before `execute_capability` for any capability
  they have not already fetched the schema for in the current session.

### 3.3 `execute_capability`

**Purpose:** actually run a capability.

| | |
|---|---|
| Input | `key: string` (required), `input: object` (optional, validated against the capability's `input_schema`) |
| Output | implementation- and capability-defined |

Rules:
- MUST fail with a clear, catchable error for unknown keys.
- Input validation against `input_schema` is RECOMMENDED but not mandated
  by this spec — implementations may delegate validation to the
  capability's own executor.

## 4. What this spec does not cover

Deliberately out of scope, left to the implementation or the product built
on top of it:

- **Authentication and authorization** — per-capability or per-source auth
  is a real requirement in production but orthogonal to the discovery
  contract above.
- **Capability registration/onboarding** — how capabilities get into the
  catalog (manual registration, OpenAPI import, an admin UI, AI-assisted
  suggestion) is entirely up to the implementer.
- **Persistence** — whether the catalog lives in memory, Postgres, or
  anywhere else is not part of this contract.
- **Versioning of individual capabilities** — this spec covers the shape of
  the 3 meta-tools, not how a capability's own schema changes over time.

## 5. Error semantics

Both `get_capability_schema` and `execute_capability` MUST distinguish
"unknown key" from other failure modes, so callers (and models) can
recover by calling `search_capabilities` again rather than retrying the
same bad key. The reference implementation raises `CapabilityNotFound` for
this case (`src/mcp_lens/registry.py`).

## 6. Versioning of this spec

This is v0.1 — draft, expect breaking changes before v1.0. Proposed changes
to the contract itself (not the reference implementation) should be raised
as issues tagged `spec` per [CONTRIBUTING.md](CONTRIBUTING.md).
