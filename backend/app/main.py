# app/main.py

from typing import Any, Literal

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from app.llm import send_to_routing_llm
from app.site import router as site_router


# ============================================================
# RESPONSE SCHEMA
# ============================================================

class Recommendation(BaseModel):
    action_type: Literal[
        "specialist_consultation",
        "additional_diagnostic_exam",
        "repeat_exam",
        "follow_up",
        "physician_review",
        "no_automatic_recommendation",
    ]

    target: str | None = None
    priority: str | None = None

    reason: str
    evidence: list[str]
    source: str | None = None


class RoutingResponse(BaseModel):
    status: Literal[
        "ok",
        "insufficient_data",
        "insufficient_guideline_context",
        "conflict_requires_review",
    ]

    recommendations: list[Recommendation]
    missing_data: list[str]
    warnings: list[str]


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Компас Routing API",
    description=(
        "Сервис маршрутизации пациентов по результатам "
        "лучевой диагностики с использованием Qwen LLM "
        "через Yandex AI Studio."
    ),
    version="3.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

# Подключаем HTML-интерфейс /app
app.include_router(site_router)


# ============================================================
# SYSTEM
# ============================================================

@app.get(
    "/",
    include_in_schema=False,
)
def root():
    """
    Главная страница сразу открывает пользовательский интерфейс.
    """
    return RedirectResponse(
        url="/app"
    )


@app.get(
    "/health",
    tags=["System"],
)
def health():
    return {
        "status": "ok",
        "service": "compass-routing-api",
        "version": "3.0.0",
    }


# ============================================================
# ROUTING
# ============================================================

@app.post(
    "/api/v1/routing",
    response_model=RoutingResponse,
    tags=["Routing"],
)
def route_study(
    payload: dict[str, Any] = Body(...),
):
    """
    Получает структурированный результат исследования
    и передаёт его в routing-модель Yandex AI Studio.

    Входной payload передаётся в LLM без изменения.
    """

    try:
        result = send_to_routing_llm(
            payload
        )

        # Проверяем, что ответ модели соответствует
        # контракту RoutingResponse.
        return RoutingResponse.model_validate(
            result
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Routing model returned response "
                f"that failed validation: {exc}"
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Routing service error: {exc}"
            ),
        ) from exc


# ============================================================
# LOCAL DEV
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8081,
        reload=True,
    )