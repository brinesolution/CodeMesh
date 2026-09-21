from app.config import Settings
from app.context.intelligence import ContextIntelligence
from app.context.schemas import MemoryUpdate, SessionContextState, SummaryUpdate
from app.models.gateway import GenerationResult, RuntimeHealth, StreamChunk
from app.models.registry import build_model_registry


class IntelligenceGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.outputs = [
            (
                '{"topic":"projectile calculator","requires_history":true,'
                '"requires_summary":true,"reference_detected":true,"recent_turns_needed":2,'
                '"memory_worthy":true,"relevant_memory_ids":[]}'
            ),
            (
                '{"changes":[{"category":"decisions","action":"add",'
                '"id":"language","text":"Use Java.","topic":"implementation"}],'
                '"memory_worthy":true}'
            ),
            '{"summary":"The user is building a projectile calculator in Java."}',
        ]

    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ):
        self.calls.append((model, messages[-1]["content"]))
        return GenerationResult(self.outputs.pop(0), model)

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        yield StreamChunk(done=True)

    async def health(self):
        return RuntimeHealth(True)

    async def list_models(self):
        return []

    async def unload(self, model: str):
        return None


async def test_all_context_tasks_resolve_the_current_router_assignment() -> None:
    settings = Settings()
    registry = build_model_registry(settings)
    gateway = IntelligenceGateway()
    intelligence = ContextIntelligence(gateway, registry, settings)
    state = SessionContextState()

    analysis, analysis_latency, analysis_model, analysis_fallback = await intelligence.analyze(
        "Do the same in Java.", state, []
    )
    registry.assign_model("router", "qwen3:1.7b")
    memory, memory_latency, memory_model, memory_fallback = await intelligence.update_memory(
        state, "Use Java.", "Java is selected.", 1
    )
    summary, summary_latency, summary_model, summary_fallback = await intelligence.update_summary(
        state, ["Use Java."], 1
    )

    assert analysis.topic == "projectile calculator"
    assert analysis.requires_history is True
    assert isinstance(memory, MemoryUpdate)
    assert isinstance(summary, SummaryUpdate)
    assert analysis_latency >= 0
    assert memory_latency >= 0
    assert summary_latency >= 0
    assert analysis_model == "qwen3:0.6b"
    assert memory_model == "qwen3:1.7b"
    assert summary_model == "qwen3:1.7b"
    assert not any((analysis_fallback, memory_fallback, summary_fallback))
    assert [model for model, _ in gateway.calls] == [
        "qwen3:0.6b",
        "qwen3:1.7b",
        "qwen3:1.7b",
    ]


async def test_analysis_normalizes_history_request_to_bounded_recent_window() -> None:
    settings = Settings(context_turns=4)
    registry = build_model_registry(settings)
    gateway = IntelligenceGateway()
    gateway.outputs[0] = (
        '{"topic":"projectile calculator","requires_history":true,'
        '"requires_summary":true,"reference_detected":true,'
        '"recent_turns_needed":0,"relevant_memory_ids":["missing"]}'
    )
    intelligence = ContextIntelligence(gateway, registry, settings)
    state = SessionContextState(summary="Existing summary")

    analysis, _, _, _ = await intelligence.analyze("Continue that", state, [])

    assert analysis.requires_history is True
    assert analysis.requires_summary is True
    assert analysis.recent_turns_needed == 4
    assert analysis.relevant_memory_ids == []


async def test_malformed_router_context_output_uses_deterministic_fallback() -> None:
    settings = Settings(context_turns=3)
    registry = build_model_registry(settings)
    gateway = IntelligenceGateway()
    gateway.outputs = ["<think>private scratchpad</think> not json", "still not json"]
    intelligence = ContextIntelligence(gateway, registry, settings)

    analysis, _, _, fallback = await intelligence.analyze(
        "Continue that", SessionContextState(), []
    )

    assert fallback is True
    assert analysis.reference_detected is True
    assert analysis.requires_history is True
    assert analysis.recent_turns_needed == 3


async def test_empty_router_analysis_still_identifies_project_topic() -> None:
    settings = Settings()
    registry = build_model_registry(settings)
    gateway = IntelligenceGateway()
    gateway.outputs = [
        '{"topic":null,"requires_history":false,"requires_summary":false,'
        '"reference_detected":false,"relevant_memory_ids":[],"recent_turns_needed":0,'
        '"memory_worthy":false}'
    ]
    intelligence = ContextIntelligence(gateway, registry, settings)

    analysis, _, _, fallback = await intelligence.analyze(
        "I am building a projectile-motion calculator with maximum height and range.",
        SessionContextState(),
        [],
    )

    assert fallback is False
    assert analysis.topic == "Projectile Motion Calculator"


async def test_historical_request_requires_prior_context_and_summary() -> None:
    settings = Settings()
    registry = build_model_registry(settings)
    gateway = IntelligenceGateway()
    gateway.outputs[0] = (
        '{"topic":null,"requires_history":false,"requires_summary":false,'
        '"reference_detected":false,"relevant_memory_ids":[],"recent_turns_needed":0,'
        '"memory_worthy":false}'
    )
    intelligence = ContextIntelligence(gateway, registry, settings)

    analysis, _, _, fallback = await intelligence.analyze(
        "What was the historical language and gravity change?",
        SessionContextState(summary="A prior project summary."),
        [],
    )

    assert fallback is False
    assert analysis.reference_detected is True
    assert analysis.requires_history is True
    assert analysis.requires_summary is True


async def test_deterministic_reference_detector_catches_artifact_references() -> None:
    settings = Settings(context_turns=6)
    registry = build_model_registry(settings)
    gateway = IntelligenceGateway()
    gateway.outputs = [
        '{"requires_history":false,"requires_summary":false,'
        '"reference_detected":false,"recent_turns_needed":0}'
    ]
    intelligence = ContextIntelligence(gateway, registry, settings)

    analysis, _, _, fallback = await intelligence.analyze(
        "Explain the function in exactly three short bullet points.",
        SessionContextState(),
        [],
    )

    assert fallback is False
    assert analysis.reference_detected is True
    assert analysis.requires_history is True
    assert analysis.recent_turns_needed == 6
