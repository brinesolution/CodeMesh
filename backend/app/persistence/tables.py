from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
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
