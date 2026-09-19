import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.orchestrator import Orchestrator
from app.main import create_app
from app.models.gateway import GenerationResult, RuntimeHealth, StreamChunk
from app.models.registry import build_model_registry
from app.persistence.repository import ChatRepository
from app.routing.service import RouterService


class StreamingFakeGateway:
    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ):
        return GenerationResult('{"expert":"coding","confidence":1,"reason":"code"}', model)

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        yield StreamChunk(text="```python\nprint('hi')\n", done=False)
        yield StreamChunk(text="```", done=False)
        yield StreamChunk(done=True)

    async def health(self):
        return RuntimeHealth(True)

    async def list_models(self):
        return []

    async def unload(self, model: str):
        return None


def test_manual_chat_stream_emits_contract_and_persists(tmp_path) -> None:
    gateway = StreamingFakeGateway()
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'stream.db'}")
    app = create_app(settings)
    models = build_model_registry(settings)
    repository = ChatRepository(settings)
    router = RouterService(gateway, models["router"], settings)
    app.state.gateway = gateway
    app.state.repository = repository
    app.state.router_service = router
    app.state.models = models
    app.state.orchestrator = Orchestrator(
        settings=settings, gateway=gateway, repository=repository, models=models, router=router
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "Write Python.", "mode": "coding"},
        )

    events = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    assert response.status_code == 200
    assert [event["type"] for event in events] == [
        "route",
        "status",
        "status",
        "token",
        "token",
        "validation",
        "metrics",
        "done",
    ]
    assert events[-1]["data"]["message"].startswith("```python")
    session_id = events[0]["data"]["session_id"]
    loaded = repository.get_session(session_id)
    assert loaded is not None
    assert [message.role for message in loaded.messages] == ["user", "assistant"]
