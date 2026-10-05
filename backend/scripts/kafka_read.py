from __future__ import annotations

import argparse
from uuid import uuid4

from confluent_kafka import Consumer

from app.kafka.config import KafkaSettings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--topic",
        choices=["output", "dlq"],
        default="output",
    )
    args = parser.parse_args()

    settings = KafkaSettings.from_env()
    topic = (
        settings.output_topic
        if args.topic == "output"
        else settings.dlq_topic
    )

    consumer = Consumer(
        {
            "bootstrap.servers": settings.bootstrap_servers,
            "group.id": f"compass-debug-{uuid4()}",
            "auto.offset.reset": "earliest",
        }
    )

    consumer.subscribe([topic])

    print(f"Reading {topic}. Ctrl+C to stop.")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print(msg.error())
                continue

            print(
                msg.value().decode("utf-8")
            )
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
