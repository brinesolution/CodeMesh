from uuid import uuid4

from sqlalchemy import select

from app.persistence.database import build_engine, build_session_factory
from app.persistence.tables import Base, ChatMessage, ChatSession, utcnow


class ChatRepository:
    def __init__(self, settings) -> None:
        self.engine = build_engine(settings)
        self.session_factory = build_session_factory(settings)
        Base.metadata.create_all(self.engine)

    def create_session(self, preferred_mode: str = "auto") -> ChatSession:
        with self.session_factory() as db:
            item = ChatSession(id=str(uuid4()), preferred_mode=preferred_mode)
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
