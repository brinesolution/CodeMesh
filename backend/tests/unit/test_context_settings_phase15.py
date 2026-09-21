from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_context_settings_default_on_and_persist_across_app_restart(tmp_path) -> None:
    database = tmp_path / "settings.db"
    settings = Settings(database_url=f"sqlite:///{database}")

    app = create_app(settings)
    with TestClient(app) as client:
        initial = client.get("/api/v1/settings/context")
        assert initial.status_code == 200
        assert all(
            initial.json()[key] is True for key in initial.json() if key.endswith("_enabled")
        )

        changed = client.patch(
            "/api/v1/settings/context",
            json={"shared_context_enabled": False, "structured_memory_enabled": False},
        )
        assert changed.status_code == 200
        assert changed.json()["shared_context_enabled"] is False
        assert changed.json()["structured_memory_enabled"] is False
        assert changed.json()["effective"]["recent_context_enabled"] is False

    restarted = create_app(settings)
    with TestClient(restarted) as client:
        persisted = client.get("/api/v1/settings/context").json()
        assert persisted["shared_context_enabled"] is False
        assert persisted["structured_memory_enabled"] is False
        assert persisted["recent_context_enabled"] is True
        assert persisted["effective"]["recent_context_enabled"] is False

        restored = client.post("/api/v1/settings/context/reset")
        assert restored.status_code == 200
        assert all(
            restored.json()[key] is True for key in restored.json() if key.endswith("_enabled")
        )
