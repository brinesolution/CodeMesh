from app.config import Settings
from app.persistence.repository import ChatRepository


def test_sessions_and_messages_survive_repository_reopen(tmp_path) -> None:
    database = tmp_path / "codemesh.db"
    settings = Settings(database_url=f"sqlite:///{database}")
    repository = ChatRepository(settings)
    created = repository.create_session("coding")
    repository.add_message(created.id, role="user", content="Write a function.")
    repository.add_message(created.id, role="assistant", content="```python\npass\n```")

    reopened = ChatRepository(settings)
    loaded = reopened.get_session(created.id)

    assert loaded is not None
    assert loaded.title == "Write a function."
    assert [message.role for message in loaded.messages] == ["user", "assistant"]
    assert reopened.recent_messages(created.id, 1)[0].role == "assistant"

