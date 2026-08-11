import asyncio

import pytest

from mcp_lens import (
    Capability,
    CapabilityNotFound,
    CapabilityRegistry,
    DuplicateCapability,
)


def make_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(
        Capability(
            key="math.add",
            description="Add two numbers",
            input_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            },
            executor=lambda a, b: a + b,
            tags=("math", "arithmetic"),
        )
    )
    registry.register(
        Capability(
            key="math.multiply",
            description="Multiply two numbers",
            input_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            },
            executor=lambda a, b: a * b,
            tags=("math", "arithmetic"),
        )
    )
    return registry


def test_search_finds_relevant_capability():
    registry = make_registry()
    results = registry.search_capabilities("add numbers")
    assert any(r["key"] == "math.add" for r in results)


def test_search_results_only_summaries_no_schema():
    registry = make_registry()
    results = registry.search_capabilities("math")
    for r in results:
        assert "input_schema" not in r


def test_search_empty_query_returns_nothing():
    registry = make_registry()
    assert registry.search_capabilities("") == []


def test_search_respects_limit():
    registry = make_registry()
    results = registry.search_capabilities("math", limit=1)
    assert len(results) == 1


def test_get_schema_returns_input_schema():
    registry = make_registry()
    schema = registry.get_capability_schema("math.multiply")
    assert schema["key"] == "math.multiply"
    assert "input_schema" in schema


def test_get_schema_unknown_key_raises():
    registry = make_registry()
    with pytest.raises(CapabilityNotFound):
        registry.get_capability_schema("does.not.exist")


def test_execute_runs_sync_executor():
    registry = make_registry()
    result = asyncio.run(registry.execute_capability("math.add", {"a": 2, "b": 3}))
    assert result == 5


def test_execute_runs_async_executor():
    registry = CapabilityRegistry()

    async def slow_add(a: int, b: int) -> int:
        return a + b

    registry.register(
        Capability(
            key="math.async_add",
            description="Add two numbers, asynchronously",
            input_schema={"type": "object", "properties": {"a": {}, "b": {}}},
            executor=slow_add,
        )
    )
    result = asyncio.run(registry.execute_capability("math.async_add", {"a": 4, "b": 5}))
    assert result == 9


def test_execute_unknown_key_raises():
    registry = make_registry()
    with pytest.raises(CapabilityNotFound):
        asyncio.run(registry.execute_capability("nope", {}))


def test_execute_with_no_input():
    registry = CapabilityRegistry()
    registry.register(
        Capability(
            key="system.ping",
            description="Health check",
            input_schema={"type": "object", "properties": {}},
            executor=lambda: "pong",
        )
    )
    result = asyncio.run(registry.execute_capability("system.ping"))
    assert result == "pong"


def test_registering_duplicate_key_raises():
    registry = make_registry()
    with pytest.raises(DuplicateCapability):
        registry.register(
            Capability(key="math.add", description="dup", input_schema={}, executor=lambda: None)
        )


def test_len_and_contains():
    registry = make_registry()
    assert len(registry) == 2
    assert "math.add" in registry
    assert "math.subtract" not in registry


def test_custom_search_fn_overrides_default():
    def always_first(catalog, query, limit):
        return catalog[:1]

    registry = CapabilityRegistry(search_fn=always_first)
    registry.register_many(
        [
            Capability(key="a.one", description="first", input_schema={}, executor=lambda: None),
            Capability(key="b.two", description="second", input_schema={}, executor=lambda: None),
        ]
    )
    results = registry.search_capabilities("anything")
    assert len(results) == 1
