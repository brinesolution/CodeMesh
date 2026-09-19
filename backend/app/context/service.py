import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.config import Settings
from app.context.extraction import extract_durable_memory
from app.context.schemas import (
    ContextAnalysis,
    MemoryChange,
    MemoryUpdate,
    SessionContextState,
    StructuredMemory,
    SummaryUpdate,
)
from app.persistence.repository import ChatRepository
from app.persistence.tables import ChatMessage


@dataclass(frozen=True)
class SummaryBatch:
    messages: list[ChatMessage]
    through_message_id: int


class ContextMemoryService:
    """Deterministic storage, bounding, and application of Router-derived context."""

    _TRIVIAL_MESSAGES = {
        "thanks",
        "thank you",
        "okay",
        "ok",
        "continue",
        "nice",
        "hello",
        "hi",
        "yes",
        "no",
    }

    def __init__(self, repository: ChatRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    def get(self, session_id: str) -> SessionContextState:
        row = self.repository.get_session_context(session_id)
        if row is None:
            return SessionContextState()
        try:
            memory = StructuredMemory.model_validate_json(row.memory_json or "{}")
        except (ValueError, TypeError, json.JSONDecodeError):
            memory = StructuredMemory()
        return SessionContextState(
            summary=row.summary or "",
            summary_through_message_id=row.summary_through_message_id,
            memory=memory,
            current_topic=row.current_topic,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
            version=max(1, row.version),
            last_router_model=row.last_router_model,
            last_memory_model=row.last_memory_model,
            last_summary_model=row.last_summary_model,
        )

    def reset(self, session_id: str) -> SessionContextState:
        """Clear only derived context; the raw messages remain untouched."""
        state = SessionContextState()
        return self._save(session_id, state)

    def record_analysis(
        self, session_id: str, analysis: ContextAnalysis, router_model: str | None
    ) -> SessionContextState:
        state = self.get(session_id)
        updated = state.model_copy(
            update={
                "current_topic": analysis.topic or state.current_topic,
                "last_router_model": router_model or state.last_router_model,
                "version": state.version + 1,
            }
        )
        return self._save(session_id, updated)

    def apply_memory_update(
        self,
        session_id: str,
        update: MemoryUpdate,
        *,
        source_message_id: int,
        router_model: str | None,
        source_text: str | None = None,
    ) -> SessionContextState:
        state = self.get(session_id)
        if self.is_trivial(source_text):
            return state

        deterministic = extract_durable_memory(
            source_text or "", current_topic=state.current_topic
        )
        if deterministic.memory_worthy:
            update = MemoryUpdate(
                changes=[*update.changes, *deterministic.changes],
                current_goal=update.current_goal or deterministic.current_goal,
                memory_worthy=True,
            )
        if not update.memory_worthy:
            return state

        memory = state.memory.model_copy(deep=True)
        for change in update.changes:
            self._apply_change(memory, change, source_message_id)
        if update.current_goal and update.current_goal.strip():
            memory.current_goal = update.current_goal.strip()[:400]
        self._cap_memory(memory)
        updated = state.model_copy(
            update={
                "memory": memory,
                "last_memory_model": router_model or state.last_memory_model,
                "last_router_model": router_model or state.last_router_model,
                "version": state.version + 1,
            }
        )
        return self._save(session_id, updated)

    def apply_summary_update(
        self,
        session_id: str,
        update: SummaryUpdate,
        *,
        through_message_id: int,
        router_model: str | None,
    ) -> SessionContextState:
        state = self.get(session_id)
        summary = update.summary.strip()[: self.settings.summary_max_chars]
        updated = state.model_copy(
            update={
                "summary": summary,
                "summary_through_message_id": through_message_id,
                "last_summary_model": router_model or state.last_summary_model,
                "last_router_model": router_model or state.last_router_model,
                "version": state.version + 1,
            }
        )
        return self._save(session_id, updated)

    def summary_batch(self, session_id: str) -> SummaryBatch | None:
        messages = self.repository.all_messages(session_id)
        if (
            sum(message.role == "user" for message in messages)
            < self.settings.summary_trigger_turns
        ):
            return None
        state = self.get(session_id)
        unsummarized = [
            message
            for message in messages
            if state.summary_through_message_id is None
            or message.id > state.summary_through_message_id
        ]
        recent_message_count = self.settings.context_turns * 2
        if len(unsummarized) <= recent_message_count:
            return None
        candidates = unsummarized[:-recent_message_count]
        if len(candidates) < 2:
            return None
        return SummaryBatch(candidates, candidates[-1].id)

    def memory_items_for_context(
        self, state: SessionContextState, analysis: ContextAnalysis
    ) -> list:
        items = [
            item
            for category in ("facts", "decisions", "constraints", "preferences", "open_tasks")
            for item in getattr(state.memory, category)
        ]
        if analysis.relevant_memory_ids:
            wanted = set(analysis.relevant_memory_ids)
            return [item for item in items if item.id in wanted]
        if analysis.topic:
            topic = analysis.topic.lower()
            topical = [item for item in items if item.topic and item.topic.lower() in topic]
            if topical:
                return topical
        return items if analysis.requires_history else []

    def context_view(self, session_id: str) -> dict[str, object] | None:
        if self.repository.get_session(session_id) is None:
            return None
        state = self.get(session_id)
        return {
            "summary": state.summary,
            "memory": state.memory.model_dump(mode="json"),
            "recent_context_turns": self.settings.context_turns,
            "summary_through_message_id": state.summary_through_message_id,
            "current_topic": state.current_topic,
            "last_updated": state.updated_at,
            "version": state.version,
            "router_model": state.last_router_model,
            "last_memory_model": state.last_memory_model,
            "last_summary_model": state.last_summary_model,
        }

    @classmethod
    def is_trivial(cls, text: str | None) -> bool:
        normalized = re.sub(r"\s+", " ", (text or "").strip().lower()).strip(".!?")
        return normalized in cls._TRIVIAL_MESSAGES

    def _apply_change(
        self, memory: StructuredMemory, change: MemoryChange, source_message_id: int
    ) -> None:
        if change.category == "topics":
            if change.action == "remove":
                memory.topics = [topic for topic in memory.topics if topic != change.text]
            elif change.text not in memory.topics:
                memory.topics.append(change.text[:120])
            return

        items = getattr(memory, change.category)
        target_id = change.id or change.replaces
        target_index = next(
            (index for index, item in enumerate(items) if target_id and item.id == target_id),
            None,
        )
        if change.action == "remove":
            setattr(memory, change.category, [item for item in items if item.id != target_id])
            return
        normalized = self._normalize(change.text)
        duplicate_index = next(
            (index for index, item in enumerate(items) if self._normalize(item.text) == normalized),
            None,
        )
        if target_index is None and duplicate_index is None:
            target_index = self._find_conflict_index(change.category, items, change.text)
        item_id = items[target_index].id if target_index is not None else change.id
        item = {
            "id": item_id,
            "text": change.text.strip(),
            "source_message_id": source_message_id,
            "updated_at": datetime.now(UTC).isoformat(),
            "topic": change.topic,
        }
        if target_index is not None:
            items[target_index] = type(items[target_index]).model_validate(item)
        elif duplicate_index is None:
            items.append(type(items[0]).model_validate(item) if items else _memory_item(item))

    def _find_conflict_index(self, category: str, items: list, text: str) -> int | None:
        if category not in {"decisions", "constraints", "preferences"}:
            return None
        lowered = self._normalize(text)
        if " instead of " in lowered:
            _, old_choice = lowered.split(" instead of ", 1)
            old_choice = old_choice.strip(" .!?\"")
            if old_choice:
                for index, item in enumerate(items):
                    if old_choice in self._normalize(item.text):
                        return index
        return None

    def _cap_memory(self, memory: StructuredMemory) -> None:
        for category in ("facts", "decisions", "constraints", "preferences", "open_tasks"):
            limit = getattr(self.settings, f"memory_max_{category}")
            setattr(memory, category, getattr(memory, category)[-limit:])
        memory.topics = memory.topics[-self.settings.memory_max_topics :]

    def _save(self, session_id: str, state: SessionContextState) -> SessionContextState:
        saved = self.repository.save_session_context(
            session_id,
            summary=state.summary,
            summary_through_message_id=state.summary_through_message_id,
            memory_json=state.memory.model_dump_json(),
            current_topic=state.current_topic,
            version=state.version,
            last_router_model=state.last_router_model,
            last_memory_model=state.last_memory_model,
            last_summary_model=state.last_summary_model,
        )
        if saved is not None and saved.updated_at is not None:
            return state.model_copy(update={"updated_at": saved.updated_at.isoformat()})
        return state

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".!?")


def _memory_item(values: dict[str, object]):
    from app.context.schemas import MemoryItem

    if values.get("id") is None:
        values = {key: value for key, value in values.items() if key != "id"}
    return MemoryItem.model_validate(values)
