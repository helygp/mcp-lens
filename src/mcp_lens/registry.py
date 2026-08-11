"""Framework-agnostic capability registry — the core of mcp-lens.

This module has zero dependency on any MCP SDK. It is the reusable engine:
register capabilities once, get three stable operations (search, schema,
execute) whose *shape* never changes no matter how many capabilities sit
behind them — 5 or 5,000.

Wrap it with an MCP server adapter (see `mcp_lens.server`) to expose it to
a model. The registry itself is plain Python and can be tested, reused, or
wrapped by any transport you want.
"""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

Executor = Callable[..., Any] | Callable[..., Awaitable[Any]]


@dataclasses.dataclass(frozen=True)
class Capability:
    """One unit of what a system can do.

    key: globally unique identifier, e.g. "billing.create_invoice". Prefix
         by source/domain to avoid collisions once you have more than one
         backend behind the same registry.
    description: natural-language description used for search matching and
         shown back to the model via get_capability_schema.
    input_schema: JSON Schema describing the arguments execute_capability
         expects. Not validated by the registry itself — bring your own
         validator in the executor, or wrap Capability.executor to enforce
         it, if you need hard guarantees.
    executor: the actual function that runs the capability. May be sync or
         async; execute_capability awaits it either way.
    tags: optional free-text tags, included in the default search scorer.
    """

    key: str
    description: str
    input_schema: dict[str, Any]
    executor: Executor
    tags: tuple[str, ...] = ()

    def default_score(self, query: str) -> float:
        """Toy relevance scorer used when no custom search_fn is supplied.

        This is intentionally simple substring/keyword matching — enough for
        demos and small catalogs. For anything beyond a few dozen
        capabilities, swap in Postgres full-text search, embeddings, or
        whatever search backend you already run, via
        `CapabilityRegistry(search_fn=...)`. The 3-meta-tool contract does
        not care how search_capabilities finds its results internally.
        """
        q = query.lower().strip()
        if not q:
            return 0.0
        haystacks = [self.key.lower(), self.description.lower(), " ".join(self.tags).lower()]
        score = 0.0
        for h in haystacks:
            if q in h:
                score += 1.0
            score += sum(0.1 for term in q.split() if term and term in h)
        return score


SearchFn = Callable[[list[Capability], str, int], list[Capability]]


class CapabilityNotFound(KeyError):
    """Raised by get_capability_schema / execute_capability for unknown keys."""


class DuplicateCapability(ValueError):
    """Raised by register() when a key is already taken."""


class CapabilityRegistry:
    """Holds N capabilities, exposes exactly 3 stable operations against them.

    This is the entire mechanism behind mcp-lens: whether N is 5 or 5,000,
    the *interface* a model sees never changes shape. Only the content
    returned by search_capabilities() grows.
    """

    def __init__(self, search_fn: SearchFn | None = None) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._search_fn = search_fn or self._default_search

    # ---- registration ----

    def register(self, capability: Capability) -> None:
        if capability.key in self._capabilities:
            raise DuplicateCapability(f"capability '{capability.key}' already registered")
        self._capabilities[capability.key] = capability

    def register_many(self, capabilities: list[Capability]) -> None:
        for capability in capabilities:
            self.register(capability)

    def unregister(self, key: str) -> None:
        self._capabilities.pop(key, None)

    @staticmethod
    def _default_search(catalog: list[Capability], query: str, limit: int) -> list[Capability]:
        scored = [(c, c.default_score(query)) for c in catalog]
        scored = [pair for pair in scored if pair[1] > 0]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    # ---- the 3 stable operations (see SPEC.md for the formal contract) ----

    def search_capabilities(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find candidate capabilities by keyword or natural language.

        Returns lightweight summaries only (key, description, tags) — never
        full schemas. Call get_capability_schema() on a result before
        calling execute_capability() with it.
        """
        catalog = list(self._capabilities.values())
        results = self._search_fn(catalog, query, limit)
        return [{"key": c.key, "description": c.description, "tags": list(c.tags)} for c in results]

    def get_capability_schema(self, key: str) -> dict[str, Any]:
        """Return the input schema for one capability, by exact key."""
        capability = self._require(key)
        return {
            "key": capability.key,
            "description": capability.description,
            "input_schema": capability.input_schema,
        }

    async def execute_capability(self, key: str, input: dict[str, Any] | None = None) -> Any:
        """Run one capability, by exact key, with the given input."""
        capability = self._require(key)
        result = capability.executor(**(input or {}))
        if inspect.isawaitable(result):
            result = await result
        return result

    # ---- internals ----

    def _require(self, key: str) -> Capability:
        try:
            return self._capabilities[key]
        except KeyError:
            raise CapabilityNotFound(
                f"no capability registered under key '{key}'. Call search_capabilities() first "
                "— capability keys are not enumerable any other way."
            ) from None

    def __len__(self) -> int:
        return len(self._capabilities)

    def __contains__(self, key: str) -> bool:
        return key in self._capabilities
