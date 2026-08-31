from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class EnquiryEvent(BaseModel):
    event_id: str
    source: Literal["gmail", "demo"] = "gmail"
    sender_name: str
    sender_email: str
    company: str | None = None
    subject: str
    body: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowDecision(BaseModel):
    service: str
    summary: str
    estimated_value_zar: int
    delivery_weeks: int
    fit_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    risks: list[str]
    next_action: Literal["qualify", "request_clarification", "decline"]
    rationale: str


class WorkflowResult(BaseModel):
    run_id: str
    status: Literal["completed", "needs_review", "failed"]
    decision: WorkflowDecision
    actions: list[dict]
