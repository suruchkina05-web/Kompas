from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from confluent_kafka import Producer

from app.kafka.config import KafkaSettings


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


@lru_cache(maxsize=1)
def get_producer() -> Producer:
    settings = KafkaSettings.from_env()

    return Producer(
        {
            "bootstrap.servers": settings.bootstrap_servers,
            "client.id": settings.client_id,
            "enable.idempotence": True,
            "acks": "all",
        }
    )


def publish_json(
    *,
    topic: str,
    key: str | None,
    payload: dict[str, Any],
) -> None:
    """
    Публикует JSON и синхронно ждёт delivery report.

    Для MVP это проще и безопаснее, чем commit входного offset
    до фактического подтверждения output message брокером.
    """
    producer = get_producer()
    delivery_error: list[Exception] = []

    def _delivery_report(err, msg):
        if err is not None:
            delivery_error.append(RuntimeError(str(err)))

    producer.produce(
        topic=topic,
        key=key.encode("utf-8") if key else None,
        value=_json_bytes(payload),
        on_delivery=_delivery_report,
    )

    remaining = producer.flush(10.0)

    if remaining:
        raise RuntimeError(
            f"Kafka producer did not flush {remaining} message(s)"
        )

    if delivery_error:
        raise delivery_error[0]
