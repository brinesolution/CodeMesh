from app.config import Settings
from app.context.schemas import MemoryUpdate
from app.context.service import ContextMemoryService
from app.persistence.repository import ChatRepository


def test_deterministic_memory_safety_net_keeps_budget_and_codename(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'durable.db'}")
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    service = ContextMemoryService(repository, settings)

    state = service.apply_memory_update(
        session_id,
        MemoryUpdate(changes=[], memory_worthy=False),
        source_message_id=1,
        router_model="qwen3:0.6b",
        source_text=(
            "Remember that the project codename is ORBIT-COPPER-72. "
            "The project budget is ₹84,000."
        ),
    )

    texts = " ".join(item.text for item in state.memory.facts)
    keys = {item.key for item in state.memory.facts}
    assert "ORBIT-COPPER-72" in texts
    assert "₹84,000" in texts
    assert {"project.codename", "project.total_budget"}.issubset(keys)


def test_deterministic_memory_replacement_keeps_current_and_historical_state(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'replacement.db'}")
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    service = ContextMemoryService(repository, settings)

    first = service.apply_memory_update(
        session_id,
        MemoryUpdate(changes=[], memory_worthy=False),
        source_message_id=1,
        router_model="qwen3:0.6b",
        source_text="The project database is MongoDB.",
    )
    current = service.apply_memory_update(
        session_id,
        MemoryUpdate(changes=[], memory_worthy=False),
        source_message_id=2,
        router_model="qwen3:0.6b",
        source_text="Replace MongoDB with PostgreSQL.",
    )

    assert first.memory.decisions[0].text == "Database = MongoDB."
    assert current.memory.decisions[0].text == "Database = PostgreSQL."
    assert [
        event.old_value
        for event in repository.list_memory_events(session_id)
        if event.old_value
    ] == [
        "Database = MongoDB."
    ]
