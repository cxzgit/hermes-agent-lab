"""The narrow point where a Responses API request reaches the client."""

from __future__ import annotations

from typing import Any


def create_response(client: Any, api_kwargs: dict[str, Any]) -> Any:
    return client.responses.create(**api_kwargs)
