from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ChatSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    preferred_mode: Mapped[str] = mapped_column(String(30), default="auto")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )
    context: Mapped["SessionContext | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False, single_parent=True
    )


class ChatMessage(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    route: Mapped[str | None] = mapped_column(String(30), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    session: Mapped[ChatSession] = relationship(back_populates="messages")


class SessionContext(Base):
    __tablename__ = "session_context"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str] = mapped_column(Text, default="")
    summary_through_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_json: Mapped[str] = mapped_column(Text, default="{}")
    current_topic: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_router_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_memory_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_summary_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    session: Mapped[ChatSession] = relationship(back_populates="context")


class ContextRun(Base):
    """Safe, bounded metadata describing an assembled specialist context."""

    __tablename__ = "context_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    current_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expert: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    router_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary_included: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    recent_message_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    approx_context_size: Mapped[int] = mapped_column(Integer, default=0)
    context_analysis_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MemoryEvent(Base):
    """Minimal append-only history for meaningful structured-memory changes."""

    __tablename__ = "memory_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    memory_id: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(30))
    event_type: Mapped[str] = mapped_column(String(20))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ApplicationSetting(Base):
    """Small durable key/value store for application-level user preferences."""

    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class MaintenanceRun(Base):
    """Lifecycle metadata for bounded post-response context maintenance."""

    __tablename__ = "maintenance_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    user_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    summary_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
