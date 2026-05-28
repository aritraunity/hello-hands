"""MCP tools for controlling IK Arms through the Flask API."""

from typing import Any

import requests
from mcp.server.fastmcp import FastMCP


FLASK_BASE_URL = "http://127.0.0.1:5000"
REQUEST_TIMEOUT_SECONDS = 10

mcp = FastMCP("IK Arms MCP")


def _post_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Post JSON to the Flask API."""
    response = requests.post(
        f"{FLASK_BASE_URL}{endpoint}",
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return dict(response.json())


def _get_json(endpoint: str) -> dict[str, Any]:
    """Get JSON from the Flask API."""
    response = requests.get(
        f"{FLASK_BASE_URL}{endpoint}",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return dict(response.json())


@mcp.tool()
def list_animations() -> dict[str, Any]:
    """List available IK Arms animations."""
    return _get_json("/api/animations")


@mcp.tool()
def play_animation(animation_name: str) -> dict[str, Any]:
    """Play an IK Arms animation by name."""
    response = requests.post(
        f"{FLASK_BASE_URL}/api/animations/{animation_name}/play",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return dict(response.json())


@mcp.tool()
def analyze_text_and_animate(text: str) -> dict[str, Any]:
    """Analyze text and trigger the best matching IK Arms animation."""
    return _post_json(
        "/api/chat/animate",
        {
            "text": text,
        },
    )


if __name__ == "__main__":
    mcp.run()