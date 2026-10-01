from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel

class Lab(BaseModel):
    code: str                 # "hemoglobin", "ferritin", "tsh", "ldl"
    value: float
    unit: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    taken_on: date

class PatientState(BaseModel):
    patient_id: str
    sex: Literal["f", "m"]
    age: int
    complaints: list[str] = []
    labs: list[Lab] = []

class Source(BaseModel):
    document: str             # название рекомендации
    section: str              # раздел
    quote: str                # короткая выдержка

class Step(BaseModel):
    id: str
    title: str                # "Сдать ферритин"
    kind: Literal["lab", "visit", "imaging", "lifestyle", "urgent"]
    zone: Literal["now", "two_weeks", "planned"]
    why: str                  # причина простым языком
    confidence: Literal["high", "medium", "doctor_decides"]
    sources: list[Source] = []
    questions_for_doctor: list[str] = []
    depends_on: list[str] = []
    skipped_reason: Optional[str] = None
    status: Literal["planned", "done", "overdue"] = "planned"

class Plan(BaseModel):
    version: int
    steps: list[Step]
    red_flags: list[str]
    verifier_notes: list[str] = []

class ClinicFunnel(BaseModel):
    got_plan: int
    reached_next_step: int
    overdue: int
    by_step: dict[str, dict[str, int]]