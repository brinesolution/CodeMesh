from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models.gateway import GenerationResult, ModelInfo, RuntimeHealth, StreamChunk


class CatalogGateway:
    async def health(self) -> RuntimeHealth:
        return RuntimeHealth(
            True,
            (
                ModelInfo("qwen3:0.6b", size_bytes=600),
                ModelInfo("smollm2:1.7b", size_bytes=1700),
                ModelInfo("qwen3:1.7b", size_bytes=1700),
                ModelInfo("qwen2.5-coder:3b", size_bytes=3000),
                ModelInfo("phi4-mini", size_bytes=4000),
            ),
        )

    async def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        structured: bool = False,
    ) -> GenerationResult:
        return GenerationResult("{}", model)

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        yield StreamChunk(done=True)

    async def unload(self, model: str) -> None:
        return None


def test_models_endpoint_discovers_and_assigns_installed_models(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'models.db'}")
    app = create_app(settings)
    app.state.gateway = CatalogGateway()

    with TestClient(app) as client:
        initial = client.get("/api/v1/models")
        assert initial.status_code == 200
        initial_payload = initial.json()
        assert {model["name"] for model in initial_payload["available_models"]} >= {"phi4-mini"}
        assert initial_payload["assignments"]["coding"] == "qwen2.5-coder:3b"

        assigned = client.put("/api/v1/models/coding", json={"model": "phi4-mini"})
        assert assigned.status_code == 200
        assert assigned.json()["assignments"]["coding"] == "phi4-mini"

        rejected = client.put("/api/v1/models/coding", json={"model": "missing:9b"})
        assert rejected.status_code == 400

        restored = client.post("/api/v1/models/reset")
        assert restored.status_code == 200
        assert restored.json()["assignments"]["coding"] == "qwen2.5-coder:3b"
