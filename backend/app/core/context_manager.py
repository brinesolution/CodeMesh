from app.persistence.repository import ChatRepository


class ContextManager:
    def __init__(self, repository: ChatRepository, context_turns: int) -> None:
        self.repository = repository
        self.context_turns = context_turns

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

