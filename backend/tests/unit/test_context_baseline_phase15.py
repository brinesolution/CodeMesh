from app.config import Settings
from app.context.schemas import ContextAnalysis, ContextIntelligenceSettings, MemoryUpdate
from app.context.service import ContextMemoryService
from app.core.context_manager import ContextManager
from app.persistence.repository import ChatRepository


def test_shared_context_keeps_recent_user_and_assistant_messages_when_router_says_no_history(
    tmp_path,
) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'baseline.db'}", context_turns=3)
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    for index in range(4):
        repository.add_message(session_id, role="user", content=f"user-{index}")
        repository.add_message(session_id, role="assistant", content=f"assistant-{index}")

    package = ContextManager(
        repository,
        settings.context_turns,
        settings=settings,
        memory_service=ContextMemoryService(repository, settings),
    ).build_specialist_context(
        session_id,
        10000,
        "new request",
        ContextAnalysis(requires_history=False, recent_turns_needed=0),
    )

    assert [message["content"] for message in package.recent_messages] == [
        "user-1",
        "assistant-1",
        "user-2",
        "assistant-2",
        "user-3",
        "assistant-3",
    ]
    assert [message["role"] for message in package.recent_messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_shared_context_keeps_newest_messages_when_an_older_answer_exceeds_budget(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'oversized.db'}", context_turns=3)
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    for index in range(4):
        repository.add_message(session_id, role="user", content=f"user-{index}")
        assistant_content = "x" * 5000 if index == 1 else f"assistant-{index}"
        repository.add_message(session_id, role="assistant", content=assistant_content)

    package = ContextManager(
        repository,
        settings.context_turns,
        settings=settings,
        memory_service=ContextMemoryService(repository, settings),
    ).build_specialist_context(
        session_id,
        1000,
        "new request",
        ContextAnalysis(requires_history=False, recent_turns_needed=0),
    )

    assert [message["content"] for message in package.recent_messages] == [
        "user-2",
        "assistant-2",
        "user-3",
        "assistant-3",
    ]


def test_context_switches_disable_shared_layers_without_erasing_raw_history(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'switches.db'}", context_turns=2)
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    repository.add_message(session_id, role="user", content="Remember the release date is Friday.")
    repository.add_message(session_id, role="assistant", content="I will remember it.")
    memory_service = ContextMemoryService(repository, settings)
    memory_service.apply_memory_update(
        session_id,
        MemoryUpdate(changes=[], memory_worthy=False),
        source_message_id=1,
        router_model=settings.router_model,
        source_text="Remember the release date is Friday.",
    )

    package = ContextManager(
        repository,
        settings.context_turns,
        settings=settings,
        memory_service=memory_service,
    ).build_specialist_context(
        session_id,
        10000,
        "What is the release date?",
        ContextAnalysis(reference_detected=True, requires_history=True),
        context_settings=ContextIntelligenceSettings(
            recent_context_enabled=False,
            structured_memory_enabled=False,
            rolling_summary_enabled=False,
            reference_resolution_enabled=False,
            smart_context_analysis_enabled=False,
            historical_changes_enabled=False,
        ),
    )

    assert package.recent_messages == []
    assert package.relevant_memory == []
    assert package.summary == ""
    assert repository.all_messages(session_id)
