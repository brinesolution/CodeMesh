import pytest

from app.config import Settings
from app.core.errors import ModelNotInstalled
from app.core.orchestrator import Orchestrator
from app.models.gateway import RuntimeHealth, StreamChunk
from app.models.registry import build_model_registry
from app.persistence.repository import ChatRepository
from app.routing.service import RouterService


class MissingModelGateway:
    async def generate(self, *, model, messages, structured=False):
        raise AssertionError("manual mode must not call the router")

    async def stream(self, *, model, messages):
        raise ModelNotInstalled("The requested Ollama model is not installed.")
        yield StreamChunk(done=True)

    async def health(self):
        return RuntimeHealth(True)

    async def list_models(self):
        return []

    async def unload(self, model):
        return None


@pytest.mark.asyncio
async def test_missing_specialist_model_becomes_stable_stream_error(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'failure.db'}")
    gateway = MissingModelGateway()
    repository = ChatRepository(settings)
    models = build_model_registry(settings)
    router = RouterService(gateway, models["router"], settings)
    orchestrator = Orchestrator(
        settings=settings,
        gateway=gateway,
        repository=repository,
        models=models,
        router=router,
    )

    events = [
        event
        async for event in orchestrator.stream_chat(
            message="Write a Python function.", mode="coding", session_id=None
        )
    ]

    assert events[-1] == {
        "type": "error",
        "data": {
            "code": "MODEL_NOT_INSTALLED",
            "message": "The requested Ollama model is not installed.",
        },
    }


@pytest.mark.asyncio
async def test_input_limit_is_rejected_before_model_call(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'limit.db'}", max_prompt_chars=1000)
    gateway = MissingModelGateway()
    repository = ChatRepository(settings)
    models = build_model_registry(settings)
    router = RouterService(gateway, models["router"], settings)
    orchestrator = Orchestrator(
        settings=settings,
        gateway=gateway,
        repository=repository,
        models=models,
        router=router,
    )

    events = [
        event
        async for event in orchestrator.stream_chat(
            message="x" * 1001, mode="coding", session_id=None
        )
    ]

    assert events == [
        {
            "type": "error",
            "data": {
                "code": "INPUT_TOO_LONG",
                "message": "Message exceeds the local input limit.",
            },
        }
    ]
