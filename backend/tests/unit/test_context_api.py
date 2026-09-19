from fastapi.testclient import TestClient

from app.config import Settings
from app.context.schemas import MemoryChange, MemoryUpdate
from app.main import create_app


def test_context_endpoint_is_session_scoped_and_empty_for_new_sessions(tmp_path) -> None:
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'context-api.db'}"))

    with TestClient(app) as client:
        first = client.post("/api/v1/sessions", json={"preferred_mode": "auto"}).json()
        second = client.post("/api/v1/sessions", json={"preferred_mode": "auto"}).json()

        first_context = client.get(f"/api/v1/sessions/{first['id']}/context")
        second_context = client.get(f"/api/v1/sessions/{second['id']}/context")

    assert first_context.status_code == 200
    assert second_context.status_code == 200
    assert first_context.json()["summary"] == ""
    assert first_context.json()["memory"]["facts"] == []
    assert second_context.json()["memory"]["facts"] == []


def test_context_endpoint_does_not_leak_memory_between_sessions(tmp_path) -> None:
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'context-isolation.db'}"))
    service = app.state.context_memory

    with TestClient(app) as client:
        first = client.post("/api/v1/sessions", json={"preferred_mode": "auto"}).json()
        second = client.post("/api/v1/sessions", json={"preferred_mode": "auto"}).json()
        service.apply_memory_update(
            first["id"],
            MemoryUpdate(
                changes=[MemoryChange(category="facts", text="First session only.")]
            ),
            source_message_id=1,
            router_model="qwen3:0.6b",
        )
        first_context = client.get(f"/api/v1/sessions/{first['id']}/context").json()
        second_context = client.get(f"/api/v1/sessions/{second['id']}/context").json()

    assert [item["text"] for item in first_context["memory"]["facts"]] == [
        "First session only."
    ]
    assert second_context["memory"]["facts"] == []


def test_context_rebuild_endpoint_returns_404_for_unknown_session(tmp_path) -> None:
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'context-rebuild-api.db'}"))

    with TestClient(app) as client:
        response = client.post("/api/v1/sessions/missing/context/rebuild")

    assert response.status_code == 404
