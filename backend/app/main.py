import sys
from pathlib import Path

# Добавляем корень проекта и папку backend в пути импорта Python
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from app.schemas import PatientState, ClinicFunnel

app = FastAPI(title="Компас API")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Сервис Компас работает"}

@app.post("/patients", response_model=PatientState)
def create_patient(patient: PatientState):
    return patient

@app.get("/patients/{patient_id}/plan")
def get_plan(patient_id: str):
    return {
        "version": 1,
        "steps": [
            {
                "id": "step_1",
                "title": "Сдать ферритин",
                "kind": "lab",
                "zone": "two_weeks",
                "why": "Необходимо оценить запасы железа в организме.",
                "confidence": "high",
                "sources": [],
                "questions_for_doctor": ["Нужно ли сдавать ОЖСС вместе с ферритином?"],
                "depends_on": [],
                "skipped_reason": None,
                "status": "planned"
            }
        ],
        "red_flags": ["Сильная одышка в покое", "Выраженная слабость"],
        "verifier_notes": []
    }

@app.get("/clinic/funnel", response_model=ClinicFunnel)
def get_clinic_funnel():
    return {
        "got_plan": 100,
        "reached_next_step": 65,
        "overdue": 15,
        "by_step": {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8081, reload=True)