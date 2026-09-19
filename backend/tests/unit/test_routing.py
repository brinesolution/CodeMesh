from app.config import Settings
from app.models.gateway import GenerationResult, RuntimeHealth, StreamChunk
from app.models.registry import build_model_registry
from app.routing.schema import ExpertRoute, parse_route_output
from app.routing.service import RouterService


class FakeGateway:
    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.calls = 0
        self.models: list[str] = []

    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ):
        self.calls += 1
        self.models.append(model)
        return GenerationResult(self.outputs[min(self.calls - 1, len(self.outputs) - 1)], model)

    async def list_models(self):
        return []

    async def health(self):
        return RuntimeHealth(True)

    async def unload(self, model: str):
        return None

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        yield StreamChunk(text="ok", done=False)
        yield StreamChunk(done=True)


def test_route_parser_ignores_qwen_thinking_wrapper() -> None:
    decision = parse_route_output(
        '<think>hidden</think>\n{"expert":"coding","confidence":0.9,"reason":"Code requested."}'
    )

    assert decision.expert is ExpertRoute.CODING
    assert decision.confidence == 0.9


async def test_router_retries_then_uses_safe_fallback() -> None:
    gateway = FakeGateway(["not json", "still not json"])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Write a Python function to sort a list.")

    assert result.expert is ExpertRoute.CODING
    assert result.routing_fallback is True
    assert gateway.calls == 2


async def test_manual_mode_never_calls_router() -> None:
    gateway = FakeGateway(['{"expert":"coding","confidence":1,"reason":"unused"}'])
    service = RouterService(gateway, build_model_registry(Settings())["router"], Settings())

    result = service.manual("stem")

    assert result.expert is ExpertRoute.STEM
    assert gateway.calls == 0


async def test_low_confidence_router_response_uses_domain_guardrail() -> None:
    gateway = FakeGateway(['{"expert":"coding","confidence":0.0,"reason":"uncertain"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("A circuit has 12 volts and 3 ohms resistance. Find current.")

    assert result.expert is ExpertRoute.STEM
    assert result.routing_fallback is True


async def test_router_reads_the_current_registry_assignment() -> None:
    gateway = FakeGateway(['{"expert":"conversation","confidence":0.9,"reason":"chat"}'])
    settings = Settings()
    registry = build_model_registry(settings)
    registry.assign_model("router", "gemma3:1b")
    service = RouterService(gateway, registry, settings)

    result = await service.route("Explain this idea in simple terms.")

    assert result.router_model == "gemma3:1b"
    assert gateway.models == ["gemma3:1b"]
