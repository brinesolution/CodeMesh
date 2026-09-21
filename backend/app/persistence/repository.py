import json
from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy import delete, select

from app.persistence.database import build_engine, build_session_factory
from app.persistence.tables import (
    ApplicationSetting,
    Base,
    ChatMessage,
    ChatSession,
    ContextRun,
    MaintenanceRun,
    MemoryEvent,
    SessionContext,
    utcnow,
)


class ChatRepository:
    def __init__(self, settings) -> None:
        self.engine = build_engine(settings)
        self.session_factory = build_session_factory(settings)
        Base.metadata.create_all(self.engine)

    def create_session(self, preferred_mode: str = "auto", title: str = "New chat") -> ChatSession:
        with self.session_factory() as db:
            item = ChatSession(
                id=str(uuid4()),
                preferred_mode=preferred_mode,
                title=title.strip()[:200] or "New chat",
            )
            item.context = SessionContext(session_id=item.id)
            db.add(item)
            db.commit()
            db.refresh(item)
            return item

    def list_sessions(self) -> list[ChatSession]:
        with self.session_factory() as db:
            return list(db.scalars(select(ChatSession).order_by(ChatSession.updated_at.desc())))

    def get_session(self, session_id: str) -> ChatSession | None:
        with self.session_factory() as db:
            item = db.get(ChatSession, session_id)
            if item is None:
                return None
            _ = item.messages
            return item

    def delete_session(self, session_id: str) -> bool:
        with self.session_factory() as db:
            item = db.get(ChatSession, session_id)
            if item is None:
                return False
            db.execute(delete(MaintenanceRun).where(MaintenanceRun.session_id == session_id))
            db.execute(delete(ContextRun).where(ContextRun.session_id == session_id))
            db.execute(delete(MemoryEvent).where(MemoryEvent.session_id == session_id))
            db.delete(item)
            db.commit()
            return True

    def add_message(self, session_id: str, **fields) -> ChatMessage:
        with self.session_factory() as db:
            message = ChatMessage(session_id=session_id, **fields)
            db.add(message)
            session = db.get(ChatSession, session_id)
            if session:
                session.updated_at = utcnow()
                if fields.get("role") == "user" and session.title == "New chat":
                    session.title = fields.get("content", "New chat").strip()[:72] or "New chat"
            db.commit()
            db.refresh(message)
            return message

    def recent_messages(self, session_id: str, limit: int) -> list[ChatMessage]:
        with self.session_factory() as db:
            query = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
                .limit(limit)
            )
            return list(reversed(list(db.scalars(query))))

    def all_messages(self, session_id: str) -> list[ChatMessage]:
        with self.session_factory() as db:
            query = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
            )
            return list(db.scalars(query))

    def get_session_context(self, session_id: str) -> SessionContext | None:
        with self.session_factory() as db:
            session = db.get(ChatSession, session_id)
            if session is None:
                return None
            context = db.get(SessionContext, session_id)
            if context is None:
                context = SessionContext(session_id=session_id)
                db.add(context)
                db.commit()
                db.refresh(context)
            return context

    def save_session_context(self, session_id: str, **fields) -> SessionContext | None:
        with self.session_factory() as db:
            session = db.get(ChatSession, session_id)
            if session is None:
                return None
            context = db.get(SessionContext, session_id)
            if context is None:
                context = SessionContext(session_id=session_id)
                db.add(context)
            for key, value in fields.items():
                setattr(context, key, value)
            context.updated_at = utcnow()
            db.commit()
            db.refresh(context)
            return context

    def add_context_run(
        self,
        session_id: str,
        *,
        current_message_id: int | None,
        response_message_id: int | None,
        expert: str,
        model: str,
        router_model: str | None,
        summary_included: bool,
        memory_ids: Sequence[str],
        recent_message_ids: Sequence[int],
        approx_context_size: int,
        context_analysis: dict[str, object],
        max_per_session: int = 64,
    ) -> ContextRun | None:
        with self.session_factory() as db:
            if db.get(ChatSession, session_id) is None:
                return None
            run = ContextRun(
                session_id=session_id,
                current_message_id=current_message_id,
                response_message_id=response_message_id,
                expert=expert,
                model=model,
                router_model=router_model,
                summary_included=summary_included,
                memory_ids_json=json.dumps(list(memory_ids)),
                recent_message_ids_json=json.dumps(list(recent_message_ids)),
                approx_context_size=max(0, approx_context_size),
                context_analysis_json=json.dumps(context_analysis),
            )
            db.add(run)
            db.flush()
            stale_ids = list(
                db.scalars(
                    select(ContextRun.id)
                    .where(ContextRun.session_id == session_id)
                    .order_by(ContextRun.created_at.desc(), ContextRun.id.desc())
                    .offset(max_per_session)
                )
            )
            if stale_ids:
                db.execute(delete(ContextRun).where(ContextRun.id.in_(stale_ids)))
            db.commit()
            db.refresh(run)
            return run

    def list_context_runs(self, session_id: str, limit: int = 64) -> list[ContextRun]:
        with self.session_factory() as db:
            query = (
                select(ContextRun)
                .where(ContextRun.session_id == session_id)
                .order_by(ContextRun.created_at.asc(), ContextRun.id.asc())
                .limit(limit)
            )
            return list(db.scalars(query))

    def add_memory_event(
        self,
        session_id: str,
        *,
        memory_id: str,
        category: str,
        event_type: str,
        old_value: str | None,
        new_value: str | None,
        source_message_id: int | None,
    ) -> MemoryEvent | None:
        with self.session_factory() as db:
            if db.get(ChatSession, session_id) is None:
                return None
            event = MemoryEvent(
                session_id=session_id,
                memory_id=memory_id,
                category=category,
                event_type=event_type,
                old_value=old_value,
                new_value=new_value,
                source_message_id=source_message_id,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event

    def get_application_setting(self, key: str) -> str | None:
        with self.session_factory() as db:
            item = db.get(ApplicationSetting, key)
            return item.value_json if item is not None else None

    def save_application_setting(self, key: str, value_json: str) -> None:
        with self.session_factory() as db:
            item = db.get(ApplicationSetting, key)
            if item is None:
                item = ApplicationSetting(key=key, value_json=value_json)
                db.add(item)
            else:
                item.value_json = value_json
                item.updated_at = utcnow()
            db.commit()

    def create_maintenance_run(
        self,
        session_id: str,
        *,
        user_message_id: int | None,
        response_message_id: int | None,
    ) -> MaintenanceRun | None:
        with self.session_factory() as db:
            if db.get(ChatSession, session_id) is None:
                return None
            run = MaintenanceRun(
                session_id=session_id,
                user_message_id=user_message_id,
                response_message_id=response_message_id,
                status="queued",
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

    def update_maintenance_run(self, run_id: int, **fields) -> MaintenanceRun | None:
        with self.session_factory() as db:
            run = db.get(MaintenanceRun, run_id)
            if run is None:
                return None
            for key, value in fields.items():
                setattr(run, key, value)
            db.commit()
            db.refresh(run)
            return run

    def list_maintenance_runs(self, session_id: str, limit: int = 64) -> list[MaintenanceRun]:
        with self.session_factory() as db:
            query = (
                select(MaintenanceRun)
                .where(MaintenanceRun.session_id == session_id)
                .order_by(MaintenanceRun.queued_at.asc(), MaintenanceRun.id.asc())
                .limit(limit)
            )
            return list(db.scalars(query))

    def list_memory_events(self, session_id: str, limit: int = 128) -> list[MemoryEvent]:
        with self.session_factory() as db:
            query = (
                select(MemoryEvent)
                .where(MemoryEvent.session_id == session_id)
                .order_by(MemoryEvent.created_at.asc(), MemoryEvent.id.asc())
                .limit(limit)
            )
            return list(db.scalars(query))
