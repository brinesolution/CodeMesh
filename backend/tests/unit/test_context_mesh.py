import json

from app.config import Settings
from app.context.schemas import MemoryChange, MemoryUpdate
from app.context.service import ContextMemoryService
from app.context_mesh.service import ContextMeshService
from app.persistence.repository import ChatRepository


def test_mesh_projection_is_current_session_scoped_and_safe(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'mesh.db'}")
    repository = ChatRepository(settings)
    current = repository.create_session("auto")
    other = repository.create_session("coding")

    first = repository.add_message(
        current.id,
        role="user",
        content="Use Java 21 for the calculator.",
    )
    repository.add_message(
        current.id,
        role="assistant",
        content="Java 21 is the selected implementation language.",
        route="coding",
        model="qwen2.5-coder:3b",
    )
    repository.add_message(other.id, role="user", content="Do not leak this chat.")

    context_memory = ContextMemoryService(repository, settings)
    context_memory.apply_memory_update(
        current.id,
        MemoryUpdate(
            changes=[
                MemoryChange(
                    category="decisions",
                    text="Language = Java 21",
                    action="add",
                    topic="calculator",
                )
            ]
        ),
        source_message_id=first.id,
        router_model="qwen3:0.6b",
        source_text="",
    )
    repository.add_context_run(
        current.id,
        current_message_id=first.id,
        response_message_id=2,
        expert="coding",
        model="qwen2.5-coder:3b",
        router_model="qwen3:0.6b",
        summary_included=True,
        memory_ids=["decision-language"],
        recent_message_ids=[first.id],
        approx_context_size=321,
        context_analysis={
            "topic": "calculator",
            "requires_history": True,
            "summary_text_snapshot": "The calculator is being implemented in Java 21.",
            "summary_through_message_id_snapshot": first.id,
            "current_goal_included": True,
            "memory_items_snapshot": [
                {
                    "id": "decision-language",
                    "text": "Language = Java 21",
                    "source_message_id": first.id,
                    "updated_at": "2026-09-20T10:08:00",
                    "topic": "calculator",
                }
            ],
            "current_goal_snapshot": "Add JUnit tests",
        },
    )

    mesh = ContextMeshService(repository, settings).get(current.id)

    assert mesh.session.id == current.id
    assert [message.id for message in mesh.messages] == [first.id, 2]
    assert all("Do not leak" not in message.content_preview for message in mesh.messages)
    assert mesh.memory.decisions[0].text == "Language = Java 21"
    assert mesh.memory.decisions[0].source_message_id == first.id
    assert mesh.latest_context_package is not None
    assert mesh.latest_context_package.expert == "coding"
    assert mesh.latest_context_package.model == "qwen2.5-coder:3b"
    assert mesh.latest_context_package.recent_message_ids == [first.id]
    assert mesh.latest_context_package.summary_text == (
        "The calculator is being implemented in Java 21."
    )
    assert mesh.latest_context_package.summary_through_message_id == first.id
    assert mesh.latest_context_package.current_goal == "Add JUnit tests"
    assert "system_prompt" not in mesh.latest_context_package.model_dump()
    assert mesh.storage.current_session_id == current.id
    assert {table.name for table in mesh.storage.tables} >= {
        "sessions",
        "messages",
        "session_context",
        "context_runs",
    }
    assert "Do not leak" not in json.dumps(mesh.model_dump(mode="json"))


def test_mesh_projection_handles_empty_session(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'empty.db'}")
    repository = ChatRepository(settings)
    session = repository.create_session()

    mesh = ContextMeshService(repository, settings).get(session.id)

    assert mesh.session.id == session.id
    assert mesh.messages == []
    assert mesh.summary.text == ""
    assert mesh.latest_context_package is None
    assert mesh.memory.facts == []
    assert mesh.storage.current_session_id == session.id


def test_mesh_projection_rejects_unknown_session(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'missing.db'}")
    repository = ChatRepository(settings)

    assert ContextMeshService(repository, settings).get("missing") is None


def test_mesh_endpoint_returns_the_current_session_projection(tmp_path) -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'mesh-api.db'}"))
    with TestClient(app) as client:
        created = client.post("/api/v1/sessions", json={"preferred_mode": "auto"}).json()
        response = client.get(f"/api/v1/sessions/{created['id']}/mesh")
        missing = client.get("/api/v1/sessions/missing/mesh")

    assert response.status_code == 200
    assert response.json()["session"]["id"] == created["id"]
    assert response.json()["storage"]["current_session_id"] == created["id"]
    assert missing.status_code == 404


def test_memory_history_only_reports_real_replacements(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'mesh-history.db'}")
    repository = ChatRepository(settings)
    session = repository.create_session()
    first = repository.add_message(session.id, role="user", content="Use Python first.")
    service = ContextMemoryService(repository, settings)

    service.apply_memory_update(
        session.id,
        MemoryUpdate(
            changes=[MemoryChange(category="decisions", text="Language = Python")]
        ),
        source_message_id=first.id,
        router_model="qwen3:0.6b",
        source_text="",
    )
    previous_id = service.get(session.id).memory.decisions[0].id
    second = repository.add_message(
        session.id,
        role="user",
        content="Use Java 21 instead of Python.",
    )
    service.apply_memory_update(
        session.id,
        MemoryUpdate(
            changes=[
                MemoryChange(
                    category="decisions",
                    text="Language = Java 21",
                    action="update",
                    id=previous_id,
                )
            ]
        ),
        source_message_id=second.id,
        router_model="qwen3:0.6b",
        source_text="",
    )

    mesh = ContextMeshService(repository, settings).get(session.id)

    assert mesh is not None
    assert [item.text for item in mesh.memory.decisions] == ["Language = Java 21"]
    assert [item.text for item in mesh.memory_history] == ["Language = Python"]


def test_delete_session_removes_mesh_audit_rows(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'mesh-delete.db'}")
    repository = ChatRepository(settings)
    session = repository.create_session()
    repository.add_context_run(
        session.id,
        current_message_id=None,
        response_message_id=None,
        expert="conversation",
        model="smollm2:1.7b",
        router_model="qwen3:0.6b",
        summary_included=False,
        memory_ids=[],
        recent_message_ids=[],
        approx_context_size=0,
        context_analysis={},
    )
    repository.add_memory_event(
        session.id,
        memory_id="fact-1",
        category="facts",
        event_type="created",
        old_value=None,
        new_value="A local fact",
        source_message_id=None,
    )

    assert repository.delete_session(session.id) is True
    assert repository.list_context_runs(session.id) == []
    assert repository.list_memory_events(session.id) == []
