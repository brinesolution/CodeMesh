from app.config import Settings
from app.core.context_manager import ContextManager
from app.persistence.repository import ChatRepository


def test_context_manager_keeps_bounded_recent_messages(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'context.db'}", context_turns=2)
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    for index in range(5):
        repository.add_message(session_id, role="user", content=f"message-{index}")

    context = ContextManager(repository, settings.context_turns).build_context(session_id, 1000)

    assert [item["content"] for item in context] == [
        "message-1",
        "message-2",
        "message-3",
        "message-4",
    ]
