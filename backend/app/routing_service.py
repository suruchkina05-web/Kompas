from __future__ import annotations

from typing import Any

from app.llm import send_to_routing_llm
from app.routing_models import RoutingResponse


def route_payload(payload: dict[str, Any]) -> RoutingResponse:
    """
    Единая бизнес-функция маршрутизации.

    Её используют оба transport adapter:
    - REST API;
    - Kafka worker.

    Входной payload передаётся в LLM без изменения.
    """
    result = send_to_routing_llm(payload)
    return RoutingResponse.model_validate(result)
