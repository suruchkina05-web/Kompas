from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.kafka.config import KafkaSettings
from app.kafka.producer import publish_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "json_file",
        help="Path to JSON payload",
    )
    args = parser.parse_args()

    payload = json.loads(
        Path(args.json_file).read_text(encoding="utf-8")
    )

    settings = KafkaSettings.from_env()
    study_iuid = payload.get("studyIUID")

    publish_json(
        topic=settings.input_topic,
        key=str(study_iuid) if study_iuid else None,
        payload=payload,
    )

    print(
        f"Sent to {settings.input_topic}: studyIUID={study_iuid}"
    )


if __name__ == "__main__":
    main()
