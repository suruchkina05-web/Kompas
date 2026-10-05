from __future__ import annotations

import json
import logging
import signal
import time
from datetime import datetime, timezone
from typing import Any

from confluent_kafka import Consumer, KafkaError, KafkaException, Message

from app.kafka.config import KafkaSettings
from app.kafka.producer import publish_json
from app.routing_service import route_payload


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("compass.kafka.worker")
_running = True


def _stop_handler(signum, frame):
    global _running
    logger.info("Stopping Kafka worker, signal=%s", signum)
    _running = False


def _decode_message(msg: Message) -> dict[str, Any]:
    raw = msg.value()

    if raw is None:
        raise ValueError("Kafka message value is empty")

    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Kafka message is not valid UTF-8 JSON: {exc}"
        ) from exc

    if not isinstance(decoded, dict):
        raise ValueError(
            "Kafka message root must be a JSON object"
        )

    return decoded


def _message_key(msg: Message, payload: dict[str, Any]) -> str | None:
    """
    Предпочитаем studyIUID как correlation key.
    Если producer upstream уже прислал Kafka key — сохраняем его.
    """
    if msg.key():
        try:
            return msg.key().decode("utf-8")
        except UnicodeDecodeError:
            pass

    study_iuid = payload.get("studyIUID")
    return str(study_iuid) if study_iuid else None


def _route_with_retry(
    payload: dict[str, Any],
    settings: KafkaSettings,
):
    last_exc: Exception | None = None

    for attempt in range(1, settings.routing_attempts + 1):
        try:
            return route_payload(payload)
        except Exception as exc:
            last_exc = exc
            logger.exception(
                "Routing attempt %s/%s failed",
                attempt,
                settings.routing_attempts,
            )

            if attempt < settings.routing_attempts:
                time.sleep(
                    settings.retry_backoff_sec * attempt
                )

    assert last_exc is not None
    raise last_exc


def _publish_success(
    *,
    settings: KafkaSettings,
    key: str | None,
    payload: dict[str, Any],
    result,
) -> None:
    envelope = {
        "studyIUID": payload.get("studyIUID"),
        "routingResult": result.model_dump(mode="json"),
    }

    publish_json(
        topic=settings.output_topic,
        key=key,
        payload=envelope,
    )


def _publish_dlq(
    *,
    settings: KafkaSettings,
    key: str | None,
    payload: dict[str, Any] | None,
    msg: Message,
    exc: Exception,
) -> None:
    envelope = {
        "failedAt": datetime.now(timezone.utc).isoformat(),
        "errorType": type(exc).__name__,
        "error": str(exc),
        "source": {
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
        },
        "studyIUID": (
            payload.get("studyIUID")
            if isinstance(payload, dict)
            else None
        ),
        "originalMessage": payload,
    }

    publish_json(
        topic=settings.dlq_topic,
        key=key,
        payload=envelope,
    )


def build_consumer(settings: KafkaSettings) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.bootstrap_servers,
            "group.id": settings.group_id,
            "client.id": settings.client_id,
            "auto.offset.reset": settings.auto_offset_reset,
            "enable.auto.commit": False,
        }
    )


def run() -> None:
    settings = KafkaSettings.from_env()
    consumer = build_consumer(settings)

    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGTERM, _stop_handler)

    consumer.subscribe([settings.input_topic])

    logger.info(
        "Kafka worker started: brokers=%s input=%s output=%s dlq=%s group=%s",
        settings.bootstrap_servers,
        settings.input_topic,
        settings.output_topic,
        settings.dlq_topic,
        settings.group_id,
    )

    try:
        while _running:
            msg = consumer.poll(settings.poll_timeout_sec)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            payload: dict[str, Any] | None = None
            key: str | None = None

            try:
                payload = _decode_message(msg)
                key = _message_key(msg, payload)

                result = _route_with_retry(
                    payload,
                    settings,
                )

                _publish_success(
                    settings=settings,
                    key=key,
                    payload=payload,
                    result=result,
                )

                # Offset подтверждаем ТОЛЬКО после успешной публикации результата.
                consumer.commit(
                    message=msg,
                    asynchronous=False,
                )

                logger.info(
                    "Processed studyIUID=%s partition=%s offset=%s status=%s",
                    payload.get("studyIUID"),
                    msg.partition(),
                    msg.offset(),
                    result.status,
                )

            except Exception as exc:
                logger.exception(
                    "Message processing failed topic=%s partition=%s offset=%s",
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                )

                try:
                    _publish_dlq(
                        settings=settings,
                        key=key,
                        payload=payload,
                        msg=msg,
                        exc=exc,
                    )

                    # После успешного DLQ publish offset можно подтвердить,
                    # иначе poison-message будет бесконечно блокировать partition.
                    consumer.commit(
                        message=msg,
                        asynchronous=False,
                    )

                    logger.warning(
                        "Message moved to DLQ: partition=%s offset=%s",
                        msg.partition(),
                        msg.offset(),
                    )

                except Exception:
                    # DLQ тоже недоступен -> offset НЕ commit'им.
                    # Сообщение будет прочитано повторно после восстановления.
                    logger.exception(
                        "DLQ publish failed; offset will not be committed"
                    )
                    time.sleep(2.0)

    finally:
        consumer.close()
        logger.info("Kafka worker stopped")


if __name__ == "__main__":
    run()
