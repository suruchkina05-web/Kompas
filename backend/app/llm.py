# app/llm.py

import json
import os
import re
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip().strip('"').strip("'")

    if not value:
        raise RuntimeError(f"В .env не найден {name}")

    return value


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(
        api_key=_required_env("YANDEX_API_KEY"),
        base_url=os.getenv(
            "YANDEX_AI_BASE_URL",
            "https://ai.api.cloud.yandex.net/v1",
        ).strip(),
        project=_required_env("YANDEX_PROJECT_ID"),
        timeout=30.0,
    )


def _clean_json(text: str) -> str:
    text = text.strip()

    text = re.sub(
        r"^```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    text = re.sub(
        r"```$",
        "",
        text,
    ).strip()

    return text


def _parse_json_response(raw_text: str) -> dict[str, Any]:
    if not raw_text:
        raise RuntimeError(
            "Yandex AI Studio вернул пустой ответ"
        )

    try:
        data = json.loads(
            _clean_json(raw_text)
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Yandex AI Studio вернул некорректный JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "Ответ Yandex AI Studio должен быть JSON-объектом"
        )

    return data


def send_to_routing_llm(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Новый routing pipeline через сохранённый prompt AI Studio.
    """

    response = _client().responses.create(
        prompt={
            "id": _required_env("YANDEX_PROMPT_ID"),
        },
        input=json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )

    return _parse_json_response(
        response.output_text
    )