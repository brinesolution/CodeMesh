from app.config import Settings
from app.context.extraction import historical_project_changes
from app.context.schemas import ContextAnalysis, SpecialistContext
from app.context.service import ContextMemoryService
from app.persistence.repository import ChatRepository


class ContextManager:
    def __init__(
        self,
        repository: ChatRepository,
        context_turns: int,
        *,
        settings: Settings | None = None,
        memory_service: ContextMemoryService | None = None,
    ) -> None:
        self.repository = repository
        self.context_turns = context_turns
        self.settings = settings or Settings(context_turns=context_turns)
        self.memory_service = memory_service or ContextMemoryService(repository, self.settings)

    def build_context(self, session_id: str, char_limit: int) -> list[dict[str, str]]:
        messages = self.repository.recent_messages(session_id, self.context_turns * 2)
        selected: list[dict[str, str]] = []
        used = 0
        for message in messages:
            if used + len(message.content) > char_limit:
                break
            selected.append({"role": message.role, "content": message.content})
            used += len(message.content)
        return selected

    def build_specialist_context(
        self,
        session_id: str,
        char_limit: int,
        current_message: str,
        analysis: ContextAnalysis,
    ) -> SpecialistContext:
        state = self.memory_service.get(session_id)
        current = current_message.strip()
        remaining = max(0, min(char_limit, self.settings.max_context_chars) - len(current))
        summary = state.summary if analysis.requires_summary else ""
        if len(summary) > remaining:
            summary = summary[:remaining]
        remaining -= len(summary)

        selected_memory = self.memory_service.memory_items_for_context(state, analysis)
        bounded_memory = []
        memory_used = 0
        for item in selected_memory:
            if memory_used + len(item.text) > min(remaining, 5000):
                break
            bounded_memory.append(item)
            memory_used += len(item.text)
        remaining -= memory_used

        recent_turns = min(max(0, analysis.recent_turns_needed), self.context_turns)
        recent_messages = self.repository.recent_messages(session_id, recent_turns * 2)
        if recent_messages and recent_messages[-1].role == "user":
            if recent_messages[-1].content.strip() == current:
                recent_messages = recent_messages[:-1]
        recent = []
        recent_message_ids = []
        recent_used = 0
        for message in recent_messages:
            if recent_used + len(message.content) > remaining:
                break
            recent.append({"role": message.role, "content": message.content})
            recent_message_ids.append(message.id)
            recent_used += len(message.content)
        historical_changes = []
        if analysis.reference_detected:
            historical_changes = historical_project_changes(
                message.content
                for message in self.repository.all_messages(session_id)
                if message.role == "user"
            )
        return SpecialistContext(
            summary=summary,
            relevant_memory=bounded_memory,
            recent_messages=recent,
            recent_message_ids=recent_message_ids,
            current_goal=state.memory.current_goal if analysis.requires_history else None,
            historical_changes=historical_changes,
            current_message=current,
        )
