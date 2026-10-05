from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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
    evidence: list[str] = Field(default_factory=list)
    source: str | None = None


class RoutingResponse(BaseModel):
    status: Literal[
        "ok",
        "insufficient_data",
        "insufficient_guideline_context",
        "conflict_requires_review",
    ]

    recommendations: list[Recommendation] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
