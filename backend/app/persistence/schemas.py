from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime
    route: str | None = None
    model: str | None = None
    route_confidence: float | None = None
    route_latency_ms: float | None = None
    generation_latency_ms: float | None = None
    validation_status: str | None = None


class SessionCreate(BaseModel):
    preferred_mode: str = Field(default="auto", max_length=30)


class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    preferred_mode: str


class SessionDetail(SessionSummary):
    messages: list[MessageView]

