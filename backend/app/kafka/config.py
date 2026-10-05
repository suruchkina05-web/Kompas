from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str
    input_topic: str
    output_topic: str
    dlq_topic: str
    group_id: str
    client_id: str
    auto_offset_reset: str
    poll_timeout_sec: float
    routing_attempts: int
    retry_backoff_sec: float

    @classmethod
    def from_env(cls) -> "KafkaSettings":
        return cls(
            bootstrap_servers=_env(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            input_topic=_env(
                "KAFKA_INPUT_TOPIC",
                "DICOMREPORTNOTIFY",
            ),
            output_topic=_env(
                "KAFKA_OUTPUT_TOPIC",
                "CLINICALROUTINGNOTIFY",
            ),
            dlq_topic=_env(
                "KAFKA_DLQ_TOPIC",
                "CLINICALROUTINGDLQ",
            ),
            group_id=_env(
                "KAFKA_GROUP_ID",
                "compass-routing-service",
            ),
            client_id=_env(
                "KAFKA_CLIENT_ID",
                "compass-routing-worker",
            ),
            auto_offset_reset=_env(
                "KAFKA_AUTO_OFFSET_RESET",
                "earliest",
            ),
            poll_timeout_sec=float(
                _env("KAFKA_POLL_TIMEOUT_SEC", "1.0")
            ),
            routing_attempts=max(
                1,
                int(_env("KAFKA_ROUTING_ATTEMPTS", "3")),
            ),
            retry_backoff_sec=max(
                0.0,
                float(_env("KAFKA_RETRY_BACKOFF_SEC", "2.0")),
            ),
        )
