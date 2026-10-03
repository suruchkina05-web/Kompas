import sys
from pathlib import Path
from typing import Optional

# ГАРАНТИЯ ИМПОРТА: принудительно вставляем корень проекта на 1-е место в sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.clinic import router as clinic_router
from app.compare import compare_with_text
from app.diff import diff_plans
from app.explain import explain_plan
from app.llm import extract_patient_state
from app.planner import build_plan
from app.schemas import Comparison, PatientPlan, PatientState, PlanDiff
from app.site import router as site_router
from app.state import merge_state
from app.verifier import verify_plan

app = FastAPI(
    title="Компас API (Третье Мнение - Лучевая диагностика)",
    description="Система маршрутизации пациентов по результатам КТ, маммографии, рентгенографии и МРТ.",
    version="2.0.0",
)

# Настройка CORS для работы браузерного UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(site_router)  # сайт пациента: /app
app.include_router(clinic_router)  # панель клиники: /clinic

PATIENTS: dict[str, PatientState] = {}
PLANS: dict[str, list[PatientPlan]] = {}


class ParseRequest(BaseModel):
    patient_id: str
    raw_text: str


class OrdersRequest(BaseModel):
    raw_text: str


class PlanDocumentResponse(BaseModel):
    state: PatientState
    plan: PatientPlan
    diff: Optional[PlanDiff] = None


@app.get("/", include_in_schema=False)
def read_root():
    """Главная страница ведёт на сайт пациента."""
    return RedirectResponse(url="/app")


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "message": "Сервис Компас (Третье Мнение) работает",
        "port": 8081,
    }


@app.post(
    "/patients/parse", response_model=PatientState, tags=["Patients Pipeline"]
)
def parse_patient_data(req: ParseRequest):
    """Только извлечение данных лучевой диагностики из текста."""
    try:
        return extract_patient_state(raw_text=req.raw_text, patient_id=req.patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/patients/documents",
    response_model=PlanDocumentResponse,
    tags=["Patients Pipeline"],
)
def add_document(req: ParseRequest):
    """Новое заключение -> обновлённая карточка -> маршрут -> проверка -> дифференциал."""
    try:
        old_state = PATIENTS.get(req.patient_id)
        text = req.raw_text
        if old_state:
            text = f"Известные данные пациента: пол {old_state.sex}, возраст {old_state.age}.\n{text}"

        new_part = extract_patient_state(raw_text=text, patient_id=req.patient_id)
        state = merge_state(old_state, new_part)
        PATIENTS[req.patient_id] = state

        history = PLANS.setdefault(req.patient_id, [])

        # Генерация плана и обогащение пояснениями
        plan = build_plan(state)
        plan = explain_plan(state, plan)

        # Валидация плана на полноту
        _ = verify_plan(state, plan)

        # Расчет изменений от предыдущей версии
        diff = diff_plans(history[-1], plan) if history else None
        history.append(plan)

        return PlanDocumentResponse(state=state, plan=plan, diff=diff)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/patients/{patient_id}/doctor-orders",
    response_model=Comparison,
    tags=["Patients Pipeline"],
)
def compare_doctor_orders(patient_id: str, req: OrdersRequest):
    """Сверка назначений врача с маршрутом по рекомендациям."""
    if patient_id not in PLANS or not PLANS[patient_id]:
        raise HTTPException(
            status_code=404,
            detail="Сначала загрузите заключения лучевой диагностики пациента",
        )
    try:
        return compare_with_text(PLANS[patient_id][-1], req.raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/patients/{patient_id}/plan",
    response_model=PatientPlan,
    tags=["Patients Pipeline"],
)
def get_plan(patient_id: str):
    if patient_id not in PLANS or not PLANS[patient_id]:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    return PLANS[patient_id][-1]


@app.post("/patients/{patient_id}/reset", tags=["Patients Pipeline"])
def reset_patient(patient_id: str):
    """Очистить данные пациента (удобно для повторов демо)."""
    PATIENTS.pop(patient_id, None)
    PLANS.pop(patient_id, None)
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8081, reload=True)