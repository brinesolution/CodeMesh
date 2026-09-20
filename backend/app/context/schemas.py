from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.routing.schema import ExpertRoute

MemoryCategory = Literal["facts", "decisions", "constraints", "preferences", "open_tasks"]
MemoryChangeCategory = Literal[
    "facts", "decisions", "constraints", "preferences", "open_tasks", "topics"
]


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=400)
    source_message_id: int | None = None
    updated_at: str = Field(default_factory=_timestamp, max_length=50)
    topic: str | None = Field(default=None, max_length=100)


class StructuredMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    facts: list[MemoryItem] = Field(default_factory=list, max_length=24)
    decisions: list[MemoryItem] = Field(default_factory=list, max_length=20)
    constraints: list[MemoryItem] = Field(default_factory=list, max_length=20)
    preferences: list[MemoryItem] = Field(default_factory=list, max_length=16)
    current_goal: str | None = Field(default=None, max_length=400)
    open_tasks: list[MemoryItem] = Field(default_factory=list, max_length=16)
    topics: list[str] = Field(default_factory=list, max_length=16)

    def is_empty(self) -> bool:
        return not any(
            (
                self.facts,
                self.decisions,
                self.constraints,
                self.preferences,
                self.current_goal,
                self.open_tasks,
                self.topics,
            )
        )


class SessionContextState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(default="", max_length=12000)
    summary_through_message_id: int | None = None
    memory: StructuredMemory = Field(default_factory=StructuredMemory)
    current_topic: str | None = Field(default=None, max_length=120)
    updated_at: str | None = None
    version: int = Field(default=1, ge=1)
    last_router_model: str | None = None
    last_memory_model: str | None = None
    last_summary_model: str | None = None


class ContextAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    expert: ExpertRoute | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    topic: str | None = Field(default=None, max_length=120)
    requires_history: bool = False
    requires_summary: bool = False
    reference_detected: bool = False
    relevant_memory_ids: list[str] = Field(default_factory=list, max_length=24)
    recent_turns_needed: int = Field(default=0, ge=0, le=12)
    memory_worthy: bool = False


class MemoryChange(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: MemoryChangeCategory
    text: str = Field(min_length=1, max_length=400)
    action: Literal["add", "update", "remove"] = "add"
    id: str | None = Field(default=None, max_length=64)
    replaces: str | None = Field(default=None, max_length=64)
    topic: str | None = Field(default=None, max_length=100)


class MemoryUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    changes: list[MemoryChange] = Field(default_factory=list, max_length=32)
    current_goal: str | None = Field(default=None, max_length=400)
    memory_worthy: bool = True


class SummaryUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(default="", max_length=12000)
    summary_through_message_id: int | None = None


class SpecialistContext(BaseModel):
    summary: str = ""
    relevant_memory: list[MemoryItem] = Field(default_factory=list)
    recent_messages: list[dict[str, str]] = Field(default_factory=list)
    current_goal: str | None = None
    historical_changes: list[str] = Field(default_factory=list)
    current_message: str

    def to_messages(self, system_prompt: str) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        if self.summary:
            messages.append({"role": "system", "content": f"SESSION SUMMARY:\n{self.summary}"})
        if self.relevant_memory:
            memory_text = "\n".join(f"- {item.text}" for item in self.relevant_memory)
            messages.append(
                {"role": "system", "content": f"RELEVANT SHARED MEMORY:\n{memory_text}"}
            )
        messages.extend(self.recent_messages)
        if self.current_goal:
            messages.append(
                {
                    "role": "system",
                    "content": f"CURRENT PROJECT GOAL:\n{self.current_goal}",
                }
            )
        if self.historical_changes:
            history = "\n".join(f"- {item}" for item in self.historical_changes)
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "HISTORICAL PROJECT CHANGES:\n"
                        f"{history}\nAnswer historical questions from this context."
                    ),
                }
            )
        messages.append({"role": "user", "content": self.current_message})
        return messages
