"""Схемы данных Pydantic для состояния пациента, маршрута и клиники."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field


def _ensure_list(v):
    """Преобразует None или отсутствие значения в пустой список."""
    if v is None:
        return []
    return v


class LabResult(BaseModel):
    code: str
    value: float
    unit: str
    taken_on: date | None = None


class ImagingFinding(BaseModel):
    modality: str  # Mammography, CT, X-ray
    finding: str
    bi_rads: str | None = None
    organ: str | None = None
    taken_on: date | None = None


class PatientState(BaseModel):
    patient_id: str
    sex: Literal["m", "f"]
    age: int
    # Защита от NoneType: если экстрактор вернёт None, автоматически подставится []
    complaints: Annotated[list[str], BeforeValidator(_ensure_list)] = Field(
        default_factory=list
    )
    labs: Annotated[list[LabResult], BeforeValidator(_ensure_list)] = Field(
        default_factory=list
    )
    findings: Annotated[list[ImagingFinding], BeforeValidator(_ensure_list)] = (
        Field(default_factory=list)
    )


class RuleSource(BaseModel):
    document: str
    section: str


class PlanStep(BaseModel):
    id: str
    title: str
    zone: Literal["now", "two_weeks", "planned"]
    confidence: Literal["high", "medium", "doctor_decides"]
    kind: Literal["lab", "visit", "imaging", "lifestyle", "urgent", "biopsy"]
    why: str
    questions_for_doctor: list[str] = Field(default_factory=list)
    sources: list[RuleSource] = Field(default_factory=list)
    skipped_reason: str | None = None


class PatientPlan(BaseModel):
    version: int
    steps: list[PlanStep]
    red_flags: list[str] = Field(default_factory=list)


class ClinicFunnel(BaseModel):
    total_patients: int
    got_plan: int
    reached_next_step: int
    overdue_patients: int
    by_step: dict[str, dict[str, int]]
    step_titles: dict[str, str]
    stuck: list[dict[str, str]]