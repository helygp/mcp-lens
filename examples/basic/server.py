"""Minimal example: 5 toy capabilities across 5 unrelated domains, exposed
through mcp-lens's 3 meta-tools instead of 5 separate MCP tools.

Run it:
    uv run examples/basic/server.py
    # or
    python examples/basic/server.py

Then point any MCP client (Claude Desktop, the MCP inspector, etc.) at it
and try: search_capabilities("send someone an email").
"""

from __future__ import annotations

from mcp_lens import Capability, CapabilityRegistry, build_server


def get_weather(city: str) -> str:
    return f"Sunny in {city}, 24°C (toy data)"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    rate = 1.08  # toy fixed rate, not real
    return {"amount": round(amount * rate, 2), "currency": to_currency}


def create_ticket(title: str, priority: str = "normal") -> dict:
    return {"id": "TCK-001", "title": title, "priority": priority, "status": "open"}


def lookup_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "shipped"}


def send_email(to: str, subject: str, body: str) -> dict:
    return {"sent": True, "to": to, "subject": subject}


registry = CapabilityRegistry()
registry.register_many(
    [
        Capability(
            key="weather.get_weather",
            description="Get current weather for a city",
            input_schema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
            executor=get_weather,
            tags=("weather", "forecast"),
        ),
        Capability(
            key="finance.convert_currency",
            description="Convert an amount from one currency to another",
            input_schema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from_currency": {"type": "string"},
                    "to_currency": {"type": "string"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
            executor=convert_currency,
            tags=("finance", "currency", "exchange"),
        ),
        Capability(
            key="support.create_ticket",
            description="Create a customer support ticket",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                },
                "required": ["title"],
            },
            executor=create_ticket,
            tags=("support", "ticket", "helpdesk"),
        ),
        Capability(
            key="commerce.lookup_order",
            description="Look up an order's status by order ID",
            input_schema={
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
            executor=lookup_order,
            tags=("commerce", "order", "shipping"),
        ),
        Capability(
            key="messaging.send_email",
            description="Send an email to someone",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
            executor=send_email,
            tags=("messaging", "email", "notify"),
        ),
    ]
)

mcp = build_server(registry, name="mcp-lens-example")

if __name__ == "__main__":
    mcp.run()
