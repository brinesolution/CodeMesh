from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.context.schemas import ContextSettingsResponse


class MeshSession(BaseModel):
    id: str
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime


class MeshMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content_preview: str
    content_length: int
    created_at: datetime
    route: str | None = None
    model: str | None = None
    route_confidence: float | None = None
    is_recent: bool = False
    is_current_prompt: bool = False


class MeshContextMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class MeshSummary(BaseModel):
    text: str = ""
    through_message_id: int | None = None
    model: str | None = None
    updated_at: datetime | None = None
    message_count: int = 0


class MeshMemoryItem(BaseModel):
    id: str
    key: str | None = None
    text: str
    source_message_id: int | None = None
    updated_at: str
    topic: str | None = None
    status: Literal["current", "superseded"] = "current"


class MeshMemoryHistory(BaseModel):
    event_id: int
    memory_id: str
    category: str
    text: str
    status: Literal["superseded"] = "superseded"
    source_message_id: int | None = None
    replaced_by_id: str | None = None
    created_at: datetime


class MeshMemory(BaseModel):
    facts: list[MeshMemoryItem] = Field(default_factory=list)
    decisions: list[MeshMemoryItem] = Field(default_factory=list)
    constraints: list[MeshMemoryItem] = Field(default_factory=list)
    preferences: list[MeshMemoryItem] = Field(default_factory=list)
    current_goal: str | None = None
    open_tasks: list[MeshMemoryItem] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)


class MeshRecentContext(BaseModel):
    message_ids: list[int] = Field(default_factory=list)
    count: int = 0


class MeshContextPackage(BaseModel):
    id: int
    expert: str
    expert_name: str
    model: str
    router_model: str | None = None
    summary_included: bool
    summary_text: str = ""
    summary_through_message_id: int | None = None
    memory_ids: list[str] = Field(default_factory=list)
    memory_items: list[MeshMemoryItem] = Field(default_factory=list)
    current_goal: str | None = None
    recent_message_ids: list[int] = Field(default_factory=list)
    recent_messages: list[MeshContextMessage] = Field(default_factory=list)
    current_message_id: int | None = None
    current_prompt: str = ""
    response_message_id: int | None = None
    approx_context_size: int = 0
    context_analysis: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MeshTimelineEvent(BaseModel):
    id: str
    type: str
    title: str
    detail: str
    created_at: datetime
    message_id: int | None = None
    node_id: str | None = None


class StorageRow(BaseModel):
    id: str
    values: dict[str, Any] = Field(default_factory=dict)


class StorageTable(BaseModel):
    name: str
    columns: list[str]
    row_count: int
    rows: list[StorageRow] = Field(default_factory=list)
    truncated: bool = False


class MeshStorage(BaseModel):
    database: str = "SQLite"
    database_name: str
    current_session_id: str
    tables: list[StorageTable] = Field(default_factory=list)


class MeshMaintenance(BaseModel):
    id: int
    status: str
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    latency_ms: float | None = None
    memory_status: str | None = None
    summary_status: str | None = None
    error: str | None = None


class ContextMeshResponse(BaseModel):
    model_config = ConfigDict(title="Context Mesh projection")

    session: MeshSession
    router: dict[str, str | None]
    summary: MeshSummary
    memory: MeshMemory
    memory_history: list[MeshMemoryHistory] = Field(default_factory=list)
    recent_context: MeshRecentContext
    messages: list[MeshMessage] = Field(default_factory=list)
    latest_context_package: MeshContextPackage | None = None
    context_settings: ContextSettingsResponse
    latest_maintenance: MeshMaintenance | None = None
    timeline: list[MeshTimelineEvent] = Field(default_factory=list)
    storage: MeshStorage
