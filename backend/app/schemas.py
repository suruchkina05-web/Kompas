from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


FindingType = Literal["mammography", "ct_chest", "xray_chest", "ultrasound", "mri", "lab"]


class Finding(BaseModel):
    modality: str = "CT"
    finding: str = ""
    bi_rads: Optional[str] = None
    organ: Optional[str] = None
    taken_on: Optional[str] = None
    code: Optional[str] = None
    val: Optional[str] = None
    finding_type: FindingType = "mammography"


class LabResult(BaseModel):
    code: str
    val: str
    unit: Optional[str] = ""
    value: Optional[str] = ""
    taken_on: Optional[str] = None


class PatientState(BaseModel):
    patient_id: str
    sex: Optional[str] = None
    age: Optional[int] = None
    complaints: list[str] = Field(default_factory=list)
    labs: list[LabResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)

    @field_validator("complaints", "labs", "findings", mode="before")
    @classmethod
    def default_none_to_list(cls, v):
        if v is None:
            return []
        return v


class StepSource(BaseModel):
    document: str
    section: str


class PlanStep(BaseModel):
    id: str
    title: str
    zone: str = "now"
    why: str = ""
    confidence: str = "high"
    kind: Literal["imaging", "consultation", "biopsy", "lab", "followup", "urgent", "lifestyle", "visit"] = "imaging"
    guideline_ref: Optional[str] = None
    trigger: Optional[str] = None
    skipped_reason: Optional[str] = None
    questions_for_doctor: list[str] = Field(default_factory=list)
    sources: list[StepSource] = Field(default_factory=list)

    @field_validator("questions_for_doctor", "sources", mode="before")
    @classmethod
    def default_none_to_list(cls, v):
        if v is None:
            return []
        return v


class PatientPlan(BaseModel):
    version: int = 1
    steps: list[PlanStep] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)

    @field_validator("steps", "red_flags", mode="before")
    @classmethod
    def default_none_to_list(cls, v):
        if v is None:
            return []
        return v


class PlanDiff(BaseModel):
    added: list[PlanStep] = Field(default_factory=list)
    removed: list[PlanStep] = Field(default_factory=list)
    unchanged: list[PlanStep] = Field(default_factory=list)


class Comparison(BaseModel):
    matched: list[PlanStep] = Field(default_factory=list)
    possibly_missing: list[PlanStep] = Field(default_factory=list)
    unclear: list[str] = Field(default_factory=list)
    questions_for_doctor: list[str] = Field(default_factory=list)


class PlanResponse(BaseModel):
    state: PatientState
    plan: PatientPlan
    diff: Optional[PlanDiff] = None


class FunnelStage(BaseModel):
    stage_id: str
    title: str
    patient_count: int = 0


class ClinicFunnel(BaseModel):
    total_patients: int = 0
    stages: list[FunnelStage] = Field(default_factory=list)


class ImagingFinding(BaseModel):
    modality: str
    finding: str
    recommendation: Optional[str] = None