import sys
from pathlib import Path

# Автоматически добавляем корень проекта и папку backend в пути импорта Python
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.schemas import PatientState, Plan, PlanDiff, Comparison
from app.llm import extract_patient_state
from app.planner import build_plan
from app.explain import explain_plan
from app.verifier import verify_plan
from app.state import merge_state
from app.diff import diff_plans
from app.compare import compare_with_text

app = FastAPI(title="Компас API")

PATIENTS: dict[str, PatientState] = {}   # пока в памяти, SQLite позже
PLANS: dict[str, list[Plan]] = {}        # история версий плана


class ParseRequest(BaseModel):
    patient_id: str
    raw_text: str


class OrdersRequest(BaseModel):
    raw_text: str


class PlanResponse(BaseModel):
    state: PatientState
    plan: Plan
    diff: Optional[PlanDiff] = None


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Сервис Компас работает"}


@app.post("/patients/parse", response_model=PatientState)
def parse_patient_data(req: ParseRequest):
    """Только извлечение данных."""
    try:
        return extract_patient_state(raw_text=req.raw_text, patient_id=req.patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patients/documents", response_model=PlanResponse)
def add_document(req: ParseRequest):
    """Новый документ -> обновлённая карточка -> маршрут -> проверка -> что изменилось."""
    try:
        old_state = PATIENTS.get(req.patient_id)
        text = req.raw_text
        if old_state:   # второй документ может не содержать пол и возраст
            text = f"Известные данные пациента: пол {old_state.sex}, возраст {old_state.age}.\n{text}"

        new_part = extract_patient_state(raw_text=text, patient_id=req.patient_id)
        state = merge_state(old_state, new_part)
        PATIENTS[req.patient_id] = state

        history = PLANS.setdefault(req.patient_id, [])
        plan = build_plan(state, version=len(history) + 1)
        plan = explain_plan(state, plan)
        plan = verify_plan(state, plan)
        diff = diff_plans(history[-1], plan, state, new_labs=new_part.labs) if history else None
        history.append(plan)

        return PlanResponse(state=state, plan=plan, diff=diff)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patients/{patient_id}/doctor-orders", response_model=Comparison)
def compare_doctor_orders(patient_id: str, req: OrdersRequest):
    """Сверка назначений врача с маршрутом по рекомендации («Третье мнение»)."""
    if patient_id not in PLANS or not PLANS[patient_id]:
        raise HTTPException(status_code=404, detail="Сначала загрузите анализы пациента")
    try:
        return compare_with_text(PLANS[patient_id][-1], req.raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients/{patient_id}/plan", response_model=Plan)
def get_plan(patient_id: str):
    if patient_id not in PLANS:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    return PLANS[patient_id][-1]


@app.post("/patients/{patient_id}/reset")
def reset_patient(patient_id: str):
    """Очистить данные пациента (удобно для повторов демо)."""
    PATIENTS.pop(patient_id, None)
    PLANS.pop(patient_id, None)
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8081, reload=True)
