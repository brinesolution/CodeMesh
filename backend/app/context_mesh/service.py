import json
from pathlib import Path
from typing import Any

from sqlalchemy import inspect

from app.config import Settings
from app.context.schemas import SessionContextState
from app.experts.registry import get_expert
from app.models.registry import ModelRegistry
from app.persistence.repository import ChatRepository
from app.persistence.tables import ChatMessage, ChatSession, ContextRun, MemoryEvent, SessionContext

from .schemas import (
    ContextMeshResponse,
    MeshContextMessage,
    MeshContextPackage,
    MeshMemory,
    MeshMemoryHistory,
    MeshMemoryItem,
    MeshMessage,
    MeshRecentContext,
    MeshSession,
    MeshStorage,
    MeshSummary,
    MeshTimelineEvent,
    StorageRow,
    StorageTable,
)


class ContextMeshService:
    """Map one selected session into safe, read-only visualizer data."""

    _PREVIEW_CHARS = 420
    _MAX_MESSAGES = 240

    def __init__(
        self,
        repository: ChatRepository,
        settings: Settings,
        models: ModelRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.models = models

    def get(self, session_id: str) -> ContextMeshResponse | None:
        session = self.repository.get_session(session_id)
        if session is None:
            return None
        context_row = self.repository.get_session_context(session_id)
        state = self._context_state(session_id, context_row)
        messages = self.repository.all_messages(session_id)
        recent_messages = self.repository.recent_messages(
            session_id, self.settings.context_turns * 2
        )
        recent_ids = [message.id for message in recent_messages]
        runs = self.repository.list_context_runs(session_id)
        memory_events = self.repository.list_memory_events(session_id)
        memory = self._memory(state)
        return ContextMeshResponse(
            session=MeshSession(
                id=session.id,
                title=session.title,
                mode=session.preferred_mode,
                created_at=session.created_at,
                updated_at=session.updated_at,
            ),
            router={"model": self._router_model(state)},
            summary=self._summary(state, messages),
            memory=memory,
            memory_history=self._memory_history(memory_events),
            recent_context=MeshRecentContext(message_ids=recent_ids, count=len(recent_ids)),
            messages=self._message_projection(messages, set(recent_ids)),
            latest_context_package=self._latest_package(runs, state, messages),
            timeline=self._timeline(messages, memory_events, runs, state),
            storage=self._storage(session, context_row, messages, runs, memory_events),
        )

    def _context_state(
        self, session_id: str, row: SessionContext | None
    ) -> SessionContextState:
        from app.context.service import ContextMemoryService

        if row is None:
            return SessionContextState()
        return ContextMemoryService(self.repository, self.settings).get(session_id)

    def _router_model(self, state: SessionContextState) -> str | None:
        if state.last_router_model:
            return state.last_router_model
        if self.models is not None:
            return self.models.get_model("router").model
        return self.settings.router_model

    def _summary(self, state: SessionContextState, messages: list[ChatMessage]) -> MeshSummary:
        return MeshSummary(
            text=state.summary,
            through_message_id=state.summary_through_message_id,
            model=state.last_summary_model,
            updated_at=self._updated_at(state.updated_at),
            message_count=sum(
                1
                for message in messages
                if message.id <= (state.summary_through_message_id or -1)
            ),
        )

    def _memory(self, state: SessionContextState) -> MeshMemory:
        values: dict[str, list[MeshMemoryItem]] = {}
        for category in ("facts", "decisions", "constraints", "preferences", "open_tasks"):
            values[category] = [
                MeshMemoryItem(
                    id=item.id,
                    text=item.text,
                    source_message_id=item.source_message_id,
                    updated_at=item.updated_at,
                    topic=item.topic,
                )
                for item in getattr(state.memory, category)
            ]
        return MeshMemory(
            **values,
            current_goal=state.memory.current_goal,
            topics=state.memory.topics,
        )

    def _message_projection(
        self, messages: list[ChatMessage], recent_ids: set[int]
    ) -> list[MeshMessage]:
        selected = self._bounded_messages(messages)
        latest_user_id = next(
            (message.id for message in reversed(messages) if message.role == "user"), None
        )
        return [
            MeshMessage(
                id=message.id,
                role=message.role,  # type: ignore[arg-type]
                content_preview=self._preview(message.content),
                content_length=len(message.content),
                created_at=message.created_at,
                route=message.route,
                model=message.model,
                route_confidence=message.route_confidence,
                is_recent=message.id in recent_ids,
                is_current_prompt=message.id == latest_user_id,
            )
            for message in selected
        ]

    def _latest_package(
        self,
        runs: list[ContextRun],
        state: SessionContextState,
        messages: list[ChatMessage],
    ) -> MeshContextPackage | None:
        if not runs:
            return None
        run = runs[-1]
        memory_by_id = {
            item.id: item
            for category in ("facts", "decisions", "constraints", "preferences", "open_tasks")
            for item in getattr(state.memory, category)
        }
        metadata = self._json_object(run.context_analysis_json)
        memory_items = self._snapshot_memory_items(metadata)
        if memory_items is None:
            memory_items = [
                MeshMemoryItem(
                    id=item.id,
                    text=item.text,
                    source_message_id=item.source_message_id,
                    updated_at=item.updated_at,
                    topic=item.topic,
                )
                for item_id in self._json_list(run.memory_ids_json)
                if (item := memory_by_id.get(str(item_id))) is not None
            ]
        message_by_id = {message.id: message for message in messages}
        recent_ids = [int(item) for item in self._json_list(run.recent_message_ids_json)]
        recent = [
            MeshContextMessage(
                id=message.id,
                role=message.role,  # type: ignore[arg-type]
                content=message.content,
                created_at=message.created_at,
            )
            for message_id in recent_ids
            if (message := message_by_id.get(message_id)) is not None
        ]
        current = message_by_id.get(run.current_message_id or -1)
        expert = get_expert(run.expert)
        summary_text = (
            str(metadata["summary_text_snapshot"])
            if "summary_text_snapshot" in metadata
            else state.summary
        )
        summary_through_message_id = self._optional_int(
            metadata.get(
                "summary_through_message_id_snapshot", state.summary_through_message_id
            )
        )
        current_goal = (
            metadata.get("current_goal_snapshot")
            if "current_goal_snapshot" in metadata
            else state.memory.current_goal
        )
        return MeshContextPackage(
            id=run.id,
            expert=run.expert,
            expert_name=expert.display_name,
            model=run.model,
            router_model=run.router_model,
            summary_included=run.summary_included,
            summary_text=summary_text if run.summary_included else "",
            summary_through_message_id=(
                summary_through_message_id if run.summary_included else None
            ),
            memory_ids=[str(item) for item in self._json_list(run.memory_ids_json)],
            memory_items=memory_items,
            current_goal=current_goal if metadata.get("current_goal_included") else None,
            recent_message_ids=recent_ids,
            recent_messages=recent,
            current_message_id=run.current_message_id,
            current_prompt=current.content if current else "",
            response_message_id=run.response_message_id,
            approx_context_size=run.approx_context_size,
            context_analysis=metadata,
            system_prompt=expert.system_prompt,
            created_at=run.created_at,
        )

    @staticmethod
    def _snapshot_memory_items(metadata: dict[str, Any]) -> list[MeshMemoryItem] | None:
        snapshot = metadata.get("memory_items_snapshot")
        if not isinstance(snapshot, list):
            return None
        items: list[MeshMemoryItem] = []
        for value in snapshot:
            if not isinstance(value, dict):
                continue
            try:
                items.append(MeshMemoryItem.model_validate(value))
            except (TypeError, ValueError):
                continue
        return items

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _memory_history(self, events: list[MemoryEvent]) -> list[MeshMemoryHistory]:
        history: list[MeshMemoryHistory] = []
        for event in events:
            if not event.old_value:
                continue
            history.append(
                MeshMemoryHistory(
                    event_id=event.id,
                    memory_id=event.memory_id,
                    category=event.category,
                    text=event.old_value,
                    source_message_id=event.source_message_id,
                    replaced_by_id=event.memory_id if event.event_type == "updated" else None,
                    created_at=event.created_at,
                )
            )
        return history

    def _timeline(
        self,
        messages: list[ChatMessage],
        memory_events: list[MemoryEvent],
        runs: list[ContextRun],
        state: SessionContextState,
    ) -> list[MeshTimelineEvent]:
        events: list[MeshTimelineEvent] = []
        for message in self._bounded_messages(messages):
            if message.role == "user":
                events.append(
                    MeshTimelineEvent(
                        id=f"message-{message.id}",
                        type="MESSAGE",
                        title=f"Message #{message.id}",
                        detail=self._preview(message.content, 180),
                        created_at=message.created_at,
                        message_id=message.id,
                        node_id=f"message-{message.id}",
                    )
                )
            elif message.route:
                events.append(
                    MeshTimelineEvent(
                        id=f"route-{message.id}",
                        type="EXPERT_SELECTED",
                        title=f"{message.route.title()} expert selected",
                        detail=(
                            f"{message.model or 'model unavailable'} generated "
                            f"response #{message.id}."
                        ),
                        created_at=message.created_at,
                        message_id=message.id,
                        node_id=f"expert-{message.route}",
                    )
                )
        for event in memory_events:
            detail = event.new_value or event.old_value or "No value recorded."
            if event.event_type == "updated" and event.old_value:
                detail = f"{event.old_value} → {event.new_value}"
            events.append(
                MeshTimelineEvent(
                    id=f"memory-event-{event.id}",
                    type=f"MEMORY_{event.event_type.upper()}",
                    title=f"{event.category.replace('_', ' ').title()} {event.event_type}",
                    detail=detail,
                    created_at=event.created_at,
                    message_id=event.source_message_id,
                    node_id=f"memory-{event.memory_id}",
                )
            )
        for run in runs:
            metadata = self._json_object(run.context_analysis_json)
            events.append(
                MeshTimelineEvent(
                    id=f"context-run-{run.id}",
                    type="CONTEXT_BUILT",
                    title="Context package built",
                    detail=(
                        f"{run.expert.title()} Expert · "
                        f"{len(self._json_list(run.recent_message_ids_json))} recent messages · "
                        f"{len(self._json_list(run.memory_ids_json))} memory items"
                        f"{' · summary included' if run.summary_included else ''}"
                    ),
                    created_at=run.created_at,
                    message_id=run.current_message_id,
                    node_id=f"context-package-{run.id}",
                )
            )
            if metadata.get("summary_updated"):
                events.append(
                    MeshTimelineEvent(
                        id=f"summary-update-{run.id}",
                        type="SUMMARY_UPDATED",
                        title="Rolling summary updated",
                        detail=(
                            "Summary through message "
                            f"{state.summary_through_message_id or '—'}."
                        ),
                        created_at=run.created_at,
                        message_id=state.summary_through_message_id,
                        node_id="summary",
                    )
                )
        if state.summary and not runs:
            events.append(
                MeshTimelineEvent(
                    id="summary-current",
                    type="SUMMARY_UPDATED",
                    title="Rolling summary available",
                    detail=f"Summary through message {state.summary_through_message_id or '—'}.",
                    created_at=self._updated_at(state.updated_at),
                    message_id=state.summary_through_message_id,
                    node_id="summary",
                )
            )
        return sorted(events, key=lambda item: (item.created_at, item.id))

    def _storage(
        self,
        session: ChatSession,
        context: SessionContext | None,
        messages: list[ChatMessage],
        runs: list[ContextRun],
        memory_events: list[MemoryEvent],
    ) -> MeshStorage:
        table_rows: list[StorageTable] = [
            self._table(
                "sessions",
                [session],
                lambda item: {
                    "id": item.id,
                    "title": item.title,
                    "preferred_mode": item.preferred_mode,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                },
            ),
            self._table(
                "messages",
                messages,
                lambda item: {
                    "id": item.id,
                    "session_id": item.session_id,
                    "role": item.role,
                    "content": self._preview(item.content, 240),
                    "created_at": item.created_at.isoformat(),
                    "route": item.route,
                    "model": item.model,
                    "route_confidence": item.route_confidence,
                },
            ),
            self._table(
                "session_context",
                [context] if context else [],
                lambda item: {
                    "session_id": item.session_id,
                    "summary": self._preview(item.summary, 240),
                    "summary_through_message_id": item.summary_through_message_id,
                    "memory_json": item.memory_json,
                    "current_topic": item.current_topic,
                    "updated_at": item.updated_at.isoformat(),
                    "version": item.version,
                },
            ),
            self._table(
                "context_runs",
                runs,
                lambda item: {
                    "id": item.id,
                    "session_id": item.session_id,
                    "current_message_id": item.current_message_id,
                    "response_message_id": item.response_message_id,
                    "expert": item.expert,
                    "model": item.model,
                    "summary_included": item.summary_included,
                    "memory_ids": item.memory_ids_json,
                    "recent_message_ids": item.recent_message_ids_json,
                    "approx_context_size": item.approx_context_size,
                    "created_at": item.created_at.isoformat(),
                },
            ),
            self._table(
                "memory_events",
                memory_events,
                lambda item: {
                    "id": item.id,
                    "session_id": item.session_id,
                    "memory_id": item.memory_id,
                    "category": item.category,
                    "event_type": item.event_type,
                    "old_value": item.old_value,
                    "new_value": item.new_value,
                    "source_message_id": item.source_message_id,
                    "created_at": item.created_at.isoformat(),
                },
            ),
        ]
        return MeshStorage(
            database_name=self._database_name(),
            current_session_id=session.id,
            tables=table_rows,
        )

    def _table(self, name: str, records: list[Any], values) -> StorageTable:
        columns = [column["name"] for column in inspect(self.repository.engine).get_columns(name)]
        rows = []
        for item in records:
            item_values = values(item)
            row_id = str(item_values.get("id", item_values.get("session_id", "row")))
            rows.append(StorageRow(id=row_id, values=item_values))
        return StorageTable(
            name=name,
            columns=columns,
            row_count=len(records),
            rows=rows,
            truncated=False,
        )

    def _database_name(self) -> str:
        if self.settings.database_url.startswith("sqlite:///"):
            return Path(self.settings.database_url.removeprefix("sqlite:///")).name
        return "codemesh.db"

    @classmethod
    def _bounded_messages(cls, messages: list[ChatMessage]) -> list[ChatMessage]:
        if len(messages) <= cls._MAX_MESSAGES:
            return messages
        return [*messages[:20], *messages[-(cls._MAX_MESSAGES - 20) :]]

    @classmethod
    def _preview(cls, value: str, limit: int | None = None) -> str:
        text = " ".join(value.split())
        max_chars = limit or cls._PREVIEW_CHARS
        return text if len(text) <= max_chars else f"{text[: max_chars - 1].rstrip()}…"

    @staticmethod
    def _json_list(value: str) -> list[Any]:
        try:
            result = json.loads(value or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
        return result if isinstance(result, list) else []

    @staticmethod
    def _json_object(value: str) -> dict[str, Any]:
        try:
            result = json.loads(value or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return result if isinstance(result, dict) else {}

    @staticmethod
    def _updated_at(value: str | None):
        from datetime import datetime

        return datetime.fromisoformat(value) if value else datetime.now()
