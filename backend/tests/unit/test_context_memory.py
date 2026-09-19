from app.config import Settings
from app.context.schemas import ContextAnalysis, MemoryChange, MemoryUpdate, SummaryUpdate
from app.context.service import ContextMemoryService
from app.core.context_manager import ContextManager
from app.persistence.repository import ChatRepository


def test_context_state_is_additive_and_survives_repository_reopen(tmp_path) -> None:
    database = tmp_path / "context.db"
    settings = Settings(database_url=f"sqlite:///{database}")
    repository = ChatRepository(settings)
    created = repository.create_session()
    repository.add_message(created.id, role="user", content="Use FastAPI.")

    service = ContextMemoryService(repository, settings)
    initial = service.get(created.id)

    assert initial.summary == ""
    assert initial.memory.is_empty()
    assert initial.summary_through_message_id is None

    reopened = ChatRepository(settings)
    assert [message.content for message in reopened.get_session(created.id).messages] == [
        "Use FastAPI."
    ]
    assert ContextMemoryService(reopened, settings).get(created.id).memory.is_empty()


def test_memory_updates_deduplicate_replace_and_respect_caps(tmp_path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'memory.db'}",
        memory_max_facts=1,
        memory_max_decisions=2,
    )
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    service = ContextMemoryService(repository, settings)

    first = service.apply_memory_update(
        session_id,
        MemoryUpdate(
            changes=[
                MemoryChange(category="facts", text="The backend uses FastAPI.", id="backend"),
                MemoryChange(category="decisions", text="Use MySQL.", id="database"),
            ]
        ),
        source_message_id=1,
        router_model="qwen3:0.6b",
    )
    duplicate = service.apply_memory_update(
        session_id,
        MemoryUpdate(changes=[MemoryChange(category="facts", text="The backend uses FastAPI.")]),
        source_message_id=2,
        router_model="qwen3:0.6b",
    )
    updated = service.apply_memory_update(
        session_id,
        MemoryUpdate(
            changes=[
                MemoryChange(
                    category="decisions",
                    action="update",
                    id="database",
                    text="Use PostgreSQL.",
                )
            ]
        ),
        source_message_id=3,
        router_model="qwen3:0.6b",
    )

    assert len(first.memory.facts) == 1
    assert len(duplicate.memory.facts) == 1
    assert [item.text for item in updated.memory.decisions] == ["Use PostgreSQL."]
    assert updated.last_memory_model == "qwen3:0.6b"


def test_memory_updates_replace_conflicting_decision_without_model_id(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'conflict.db'}")
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    service = ContextMemoryService(repository, settings)

    service.apply_memory_update(
        session_id,
        MemoryUpdate(
            changes=[MemoryChange(category="decisions", text="Use MySQL.")]
        ),
        source_message_id=1,
        router_model="qwen3:0.6b",
    )
    updated = service.apply_memory_update(
        session_id,
        MemoryUpdate(
            changes=[
                MemoryChange(
                    category="decisions", text="Use PostgreSQL instead of MySQL."
                )
            ]
        ),
        source_message_id=2,
        router_model="qwen3:0.6b",
    )

    assert [item.text for item in updated.memory.decisions] == [
        "Use PostgreSQL instead of MySQL."
    ]
    assert updated.memory.decisions[0].source_message_id == 2


def test_context_update_returns_persisted_timestamp(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'timestamp.db'}")
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    service = ContextMemoryService(repository, settings)

    updated = service.record_analysis(
        session_id,
        ContextAnalysis(topic="testing"),
        "qwen3:0.6b",
    )

    assert updated.updated_at is not None
    assert service.get(session_id).updated_at == updated.updated_at


def test_summary_batch_contains_only_messages_leaving_recent_window(tmp_path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'summary.db'}",
        context_turns=3,
        summary_trigger_turns=5,
    )
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    for index in range(8):
        repository.add_message(session_id, role="user", content=f"user-{index}")
        repository.add_message(session_id, role="assistant", content=f"assistant-{index}")

    batch = ContextMemoryService(repository, settings).summary_batch(session_id)

    assert batch is not None
    assert [message.content for message in batch.messages] == [
        "user-0",
        "assistant-0",
        "user-1",
        "assistant-1",
        "user-2",
        "assistant-2",
        "user-3",
        "assistant-3",
        "user-4",
        "assistant-4",
    ]
    assert batch.messages[-1].content != "assistant-7"


def test_long_conversation_keeps_raw_history_and_bounds_derived_context(tmp_path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'long.db'}",
        context_turns=6,
        summary_trigger_turns=8,
    )
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    for index in range(40):
        repository.add_message(session_id, role="user", content=f"User turn {index}.")
        repository.add_message(session_id, role="assistant", content=f"Assistant turn {index}.")
    service = ContextMemoryService(repository, settings)

    batch = service.summary_batch(session_id)
    assert batch is not None
    assert len(batch.messages) == 68
    service.apply_summary_update(
        session_id,
        SummaryUpdate(summary="A bounded summary of the earlier conversation."),
        through_message_id=batch.through_message_id,
        router_model="qwen3:0.6b",
    )

    assert len(repository.all_messages(session_id)) == 80
    assert service.summary_batch(session_id) is None
    assert len(service.get(session_id).summary) < settings.summary_max_chars


def test_specialist_context_includes_selected_memory_once_and_current_request_once(
    tmp_path,
) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'package.db'}", context_turns=2)
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    repository.add_message(session_id, role="user", content="We chose Java.")
    repository.add_message(session_id, role="assistant", content="Java is the current choice.")
    repository.add_message(session_id, role="user", content="Now implement it.")
    service = ContextMemoryService(repository, settings)
    state = service.apply_memory_update(
        session_id,
        MemoryUpdate(
            changes=[MemoryChange(category="decisions", text="Use Java.", id="language")]
        ),
        source_message_id=1,
        router_model="qwen3:0.6b",
    )
    analysis = ContextAnalysis(
        requires_history=True,
        requires_summary=False,
        relevant_memory_ids=[state.memory.decisions[0].id],
        recent_turns_needed=2,
        reference_detected=True,
    )

    package = ContextManager(
        repository,
        settings.context_turns,
        settings=settings,
        memory_service=service,
    ).build_specialist_context(
        session_id,
        5000,
        "Now implement it.",
        analysis,
    )
    messages = package.to_messages("SYSTEM")
    contents = [message["content"] for message in messages]

    assert contents[0] == "SYSTEM"
    assert sum(content == "Now implement it." for content in contents) == 1
    assert any("Use Java." in content for content in contents)
    assert all("Now implement it." not in content for content in contents[1:-1])
