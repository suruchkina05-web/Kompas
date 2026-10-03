"""Pydantic-схемы Kompas. Текущий MVP ограничен маммографией."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field


def _ensure_list(value):
    return [] if value is None else value


ClinicalContext = Literal[
    "screening",
    "palpable_mass",
    "breast_pain",
    "nipple_discharge",
    "skin_or_nipple_changes",
    "abnormal_ultrasound",
    "abnormal_previous_mammography",
    "suspected_breast_cancer",
    "confirmed_breast_cancer",
    "follow_up_after_breast_cancer_treatment",
    "inflammatory_breast_disease",
    "ovarian_cancer_workup",
    "cancer_of_unknown_primary",
    "menopausal_HRT_monitoring",
    "unknown",
]


class LabResult(BaseModel):
    """Оставлено для обратной совместимости; в mammography-MVP не используется."""

    code: str
    value: float
    unit: str
    taken_on: date | None = None


class BreastAssessment(BaseModel):
    """Результат маммографии отдельно для одной молочной железы."""

    birads: int | None = Field(default=None, ge=0, le=6)
    birads_subcategory: Literal["4A", "4B", "4C"] | None = None
    acr_density: Literal["A", "B", "C", "D"] | None = None
    findings: Annotated[list[str], BeforeValidator(_ensure_list)] = Field(default_factory=list)
    locations: Annotated[list[str], BeforeValidator(_ensure_list)] = Field(default_factory=list)


class MammographyResult(BaseModel):
    modality: Literal["Mammography"] = "Mammography"
    taken_on: date | None = None
    right_breast: BreastAssessment = Field(default_factory=BreastAssessment)
    left_breast: BreastAssessment = Field(default_factory=BreastAssessment)
    comparison_with_previous: str | None = None
    previous_mammography_date: date | None = None
    recommendation: str | None = None
    clinical_context: ClinicalContext = "unknown"


class ImagingFinding(BaseModel):
    """Legacy-модель для совместимости старых модулей. Новые правила ее не используют."""

    modality: Literal["Mammography", "Unknown"] = "Unknown"
    finding: str
    bi_rads: str | None = None
    organ: str | None = None
    taken_on: date | None = None


class PatientState(BaseModel):
    patient_id: str
    sex: Literal["m", "f"] | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    clinical_context: ClinicalContext = "unknown"
    complaints: Annotated[list[str], BeforeValidator(_ensure_list)] = Field(default_factory=list)
    risk_factors: Annotated[list[str], BeforeValidator(_ensure_list)] = Field(default_factory=list)
    metastatic_sites: Annotated[list[str], BeforeValidator(_ensure_list)] = Field(default_factory=list)
    no_response_to_antiinflammatory_treatment: bool | None = None
    mammography: Annotated[list[MammographyResult], BeforeValidator(_ensure_list)] = Field(default_factory=list)
    labs: Annotated[list[LabResult], BeforeValidator(_ensure_list)] = Field(default_factory=list)
    findings: Annotated[list[ImagingFinding], BeforeValidator(_ensure_list)] = Field(default_factory=list)


class RuleSource(BaseModel):
    source_id: str | None = None
    document: str
    section: str
    page: int | None = None
    recommendation_strength: str | None = None
    evidence_level: str | None = None


class PlanStep(BaseModel):
    id: str
    title: str
    zone: Literal["now", "two_weeks", "planned"] = "planned"
    confidence: Literal["high", "medium", "doctor_decides"] = "medium"
    kind: Literal["visit", "imaging", "biopsy"] = "imaging"
    why: str = ""
    trigger: str = ""
    questions_for_doctor: list[str] = Field(default_factory=list)
    sources: list[RuleSource] = Field(default_factory=list)
    skipped_reason: str | None = None


class PlanResponse(BaseModel):
    patient_id: str
    version: int = Field(default=1, ge=1)
    steps: list[PlanStep] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    verifier_notes: list[str] = Field(default_factory=list)


Plan = PlanResponse
Step = PlanStep
PatientPlan = PlanResponse


class PlanDiff(BaseModel):
    added: list[PlanStep] = Field(default_factory=list)
    removed: list[PlanStep] = Field(default_factory=list)
    explanation: str = ""


class Comparison(BaseModel):
    matched: list[PlanStep] = Field(default_factory=list)
    possibly_missing: list[PlanStep] = Field(default_factory=list)
    unclear: list[str] = Field(default_factory=list)
    questions_for_doctor: list[str] = Field(default_factory=list)


class ClinicFunnel(BaseModel):
    total_patients: int
    got_plan: int
    reached_next_step: int
    overdue_patients: int
    by_step: dict[str, dict[str, int]]
    step_titles: dict[str, str]
    stuck: list[dict[str, str]]
