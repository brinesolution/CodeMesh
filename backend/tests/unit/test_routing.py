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


async def test_artifact_generation_intent_overrides_domain_noun() -> None:
    gateway = FakeGateway(['{"expert":"stem","confidence":0.9,"reason":"JSON uses structure."}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route(
        "Write a JSON configuration representing the current requirements."
    )

    assert result.expert is ExpertRoute.CODING
    assert result.routing_fallback is True


async def test_high_confidence_conversation_cannot_hide_obvious_stem_request() -> None:
    gateway = FakeGateway(['{"expert":"conversation","confidence":0.95,"reason":"chat"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Calculate the acceleration when a 20 N force acts on 5 kg.")

    assert result.expert is ExpertRoute.STEM
    assert result.routing_fallback is True


async def test_high_confidence_coding_cannot_hide_obvious_stem_request() -> None:
    gateway = FakeGateway(['{"expert":"coding","confidence":0.95,"reason":"code"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Integrate 2x with respect to x.")

    assert result.expert is ExpertRoute.STEM
    assert result.routing_fallback is True


async def test_high_confidence_non_artifact_route_is_preserved() -> None:
    gateway = FakeGateway(['{"expert":"stem","confidence":0.95,"reason":"science"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Explain why seasons change on Earth.")

    assert result.expert is ExpertRoute.STEM
    assert result.routing_fallback is False


async def test_generic_explanation_guardrail_corrects_neutral_router_drift() -> None:
    gateway = FakeGateway(['{"expert":"stem","confidence":0.95,"reason":"science"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Explain why sleep matters for learning.")

    assert result.expert is ExpertRoute.CONVERSATION
    assert result.routing_fallback is True


async def test_current_fact_questions_are_not_misclassified_as_electricity() -> None:
    gateway = FakeGateway(['{"expert":"stem","confidence":0.95,"reason":"science"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("What database is current and what was the previous one?")

    assert result.expert is ExpertRoute.CONVERSATION
    assert result.routing_fallback is True


async def test_project_offline_and_goal_statements_stay_conversational() -> None:
    gateway = FakeGateway(['{"expert":"stem","confidence":0.95,"reason":"science"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    offline = await service.route(
        "The project must work fully offline and must not use external APIs."
    )
    goal = await service.route("The current goal is to add unit tests for this service.")

    assert offline.expert is ExpertRoute.CONVERSATION
    assert goal.expert is ExpertRoute.CONVERSATION
    assert offline.routing_fallback is True
    assert goal.routing_fallback is True


async def test_gravity_range_reference_stays_stem() -> None:
    gateway = FakeGateway(['{"expert":"coding","confidence":0.95,"reason":"code"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route(
        "Using the expected value, verify the horizontal range for 30 m/s at 40° "
        "with the current gravity."
    )

    assert result.expert is ExpertRoute.STEM
    assert result.routing_fallback is True


async def test_historical_value_question_stays_conversational() -> None:
    gateway = FakeGateway(['{"expert":"stem","confidence":0.95,"reason":"science"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("What language and gravity values changed historically?")

    assert result.expert is ExpertRoute.CONVERSATION
    assert result.routing_fallback is True


async def test_junit_test_artifact_routes_to_coding() -> None:
    gateway = FakeGateway(['{"expert":"conversation","confidence":0.95,"reason":"chat"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Write the JUnit tests we planned using the expected value.")

    assert result.expert is ExpertRoute.CODING
    assert result.routing_fallback is True


async def test_database_replacement_without_database_word_stays_conversational() -> None:
    gateway = FakeGateway(['{"expert":"coding","confidence":0.95,"reason":"code"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route(
        "Replace SQLite with PostgreSQL while keeping the same local workflow."
    )

    assert result.expert is ExpertRoute.CONVERSATION
    assert result.routing_fallback is True


async def test_request_rate_input_check_routes_to_coding() -> None:
    gateway = FakeGateway(['{"expert":"conversation","confidence":0.95,"reason":"chat"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Add an input check that rejects negative request rates.")

    assert result.expert is ExpertRoute.CODING
    assert result.routing_fallback is True


async def test_input_check_followup_question_stays_conversational() -> None:
    gateway = FakeGateway(['{"expert":"coding","confidence":0.95,"reason":"code"}'])
    settings = Settings()
    service = RouterService(gateway, build_model_registry(settings)["router"], settings)

    result = await service.route("Why should that input check be kept?")

    assert result.expert is ExpertRoute.CONVERSATION
    assert result.routing_fallback is True
