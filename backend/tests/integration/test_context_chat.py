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


class ReferenceContextGateway(ContextChatGateway):
    def __init__(self) -> None:
        super().__init__()
        self.responses = [
            "```python\ndef calculate():\n    return 42\n```",
            "```java\nstatic int calculate() { return 42; }\n```",
        ]

    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ):
        system = messages[0]["content"]
        if "context analyst" in system:
            return GenerationResult(
                '{"requires_history":false,"recent_turns_needed":0}', model
            )
        if "memory extractor" in system:
            return GenerationResult('{"changes":[],"memory_worthy":false}', model)
        return GenerationResult('{"summary":""}', model)

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        self.stream_messages.append(messages)
        yield StreamChunk(text=self.responses.pop(0))
        yield StreamChunk(done=True)


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
    assert metrics["context"]["session_id"] == session_id
    assert metrics["context"]["router_model"] == settings.router_model
    assert metrics["context"]["specialist_model"] == settings.chat_model
    assert metrics["context"]["recent_message_roles"] == ["user", "assistant"]
    assert metrics["context"]["structured_memory_included"] is True
    assert metrics["context"]["memory_item_count"] >= 1
    assert metrics["context"]["memory_update_status"] == "updated"
    assert metrics["context"]["summary_update_status"] == "not_due"


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


async def test_reference_request_receives_previous_assistant_implementation(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'context-reference.db'}")
    gateway = ReferenceContextGateway()
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
        message="Create a Python implementation using functions.",
        mode="coding",
        session_id=None,
    )
    await orchestrator.chat(
        message="Rewrite the previous implementation accordingly.",
        mode="coding",
        session_id=first["session_id"],
    )

    second_contents = [item["content"] for item in gateway.stream_messages[1]]
    assert any("def calculate()" in content for content in second_contents)
    assert (
        sum(
            content == "Rewrite the previous implementation accordingly."
            for content in second_contents
        )
        == 1
    )
