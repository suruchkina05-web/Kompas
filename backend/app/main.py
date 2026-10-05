from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routing_models import RoutingResponse
from app.routing_service import route_payload
from app.site import router as site_router


app = FastAPI(
    title="Компас Routing API",
    description=(
        "Сервис маршрутизации пациентов по результатам лучевой диагностики. "
        "REST и Kafka используют единый routing pipeline."
    ),
    version="3.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

app.include_router(site_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app")


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "service": "compass-routing-api",
        "version": "3.1.0",
    }


@app.get("/ready", tags=["System"])
def ready():
    return {
        "status": "ready",
        "service": "compass-routing-api",
    }


@app.post(
    "/api/v1/routing",
    response_model=RoutingResponse,
    tags=["Routing"],
)
def route_study(
    payload: dict[str, Any] = Body(...),
):
    """
    REST adapter.

    Тот же route_payload() используется Kafka worker'ом.
    """
    try:
        return route_payload(payload)

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
            detail=f"Routing service error: {exc}",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8081,
        reload=True,
    )
