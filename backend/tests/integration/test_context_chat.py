from app.config import Settings
from app.core.orchestrator import Orchestrator
from app.models.gateway import GenerationResult, RuntimeHealth, StreamChunk
from app.models.registry import build_model_registry
from app.persistence.repository import ChatRepository
from app.routing.service import RouterService


class ContextChatGateway:
    def __init__(self) -> None:
        self.analysis_calls = 0
        self.stream_messages: list[list[dict[str, str]]] = []

    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ):
        system = messages[0]["content"]
        if "context analyst" in system:
            self.analysis_calls += 1
            payload = (
                '{"requires_history":true,"recent_turns_needed":2}'
                if self.analysis_calls > 1
                else '{"requires_history":false,"recent_turns_needed":0}'
            )
        elif "memory extractor" in system:
            payload = (
                '{"changes":[{"category":"preferences",'
                '"text":"Prefer concise answers."}],"memory_worthy":true}'
            )
        else:
            payload = '{"summary":"A concise answer preference was established."}'
        return GenerationResult(payload, model)

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        self.stream_messages.append(messages)
        yield StreamChunk(text="Answer.")
        yield StreamChunk(done=True)

    async def health(self):
        return RuntimeHealth(True)

    async def list_models(self):
        return []

    async def unload(self, model: str):
        return None


async def test_chat_uses_shared_context_and_emits_context_metrics(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'context-chat.db'}")
    gateway = ContextChatGateway()
    repository = ChatRepository(settings)
    models = build_model_registry(settings)
    router = RouterService(gateway, models, settings)
    orchestrator = Orchestrator(
        settings=settings,
        gateway=gateway,
        repository=repository,
        models=models,
        router=router,
    )

    first = await orchestrator.chat(
        message="Remember this preference.", mode="conversation", session_id=None
    )
    session_id = first["session_id"]
    second = await orchestrator.chat(
        message="Now use that preference.", mode="conversation", session_id=session_id
    )

    second_contents = [item["content"] for item in gateway.stream_messages[1]]
    metrics = second["metrics"]
    assert sum(content == "Now use that preference." for content in second_contents) == 1
    assert any("RELEVANT SHARED MEMORY" in content for content in second_contents)
    assert metrics["routing_context_latency_ms"] >= 0
    assert metrics["memory_update_latency_ms"] >= 0
    assert metrics["summary_update_latency_ms"] == 0.0
    assert metrics["specialist_generation_latency_ms"] >= 0


async def test_context_maintenance_failure_does_not_discard_answer(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'context-maintenance.db'}")
    gateway = ContextChatGateway()
    repository = ChatRepository(settings)
    models = build_model_registry(settings)
    router = RouterService(gateway, models, settings)
    orchestrator = Orchestrator(
        settings=settings,
        gateway=gateway,
        repository=repository,
        models=models,
        router=router,
    )

    async def broken_memory_update(*args, **kwargs):
        raise RuntimeError("simulated context maintenance failure")

    orchestrator.context_intelligence.update_memory = broken_memory_update
    result = await orchestrator.chat(
        message="Keep the answer short.", mode="conversation", session_id=None
    )

    assert result["message"] == "Answer."
    assert result["metrics"]["memory_update_latency_ms"] == 0.0
