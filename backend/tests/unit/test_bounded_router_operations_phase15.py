import asyncio
import time

from app.config import Settings
from app.context.intelligence import ContextIntelligence
from app.context.schemas import SessionContextState
from app.models.gateway import GenerationResult
from app.models.registry import build_model_registry
from app.routing.schema import ExpertRoute
from app.routing.service import RouterService


class SlowStructuredGateway:
    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ) -> GenerationResult:
        await asyncio.sleep(5)
        return GenerationResult("{}", model)


async def test_context_analysis_deadline_returns_deterministic_fallback() -> None:
    settings = Settings(context_analysis_timeout_seconds=1.1, context_turns=3)
    registry = build_model_registry(settings)
    intelligence = ContextIntelligence(SlowStructuredGateway(), registry, settings)

    started = time.perf_counter()
    analysis, latency, _, fallback = await intelligence.analyze(
        "Calculate the square root of 144.", SessionContextState(), []
    )
    elapsed = time.perf_counter() - started

    assert elapsed < 2.0
    assert latency < 1800
    assert fallback is True
    assert analysis.expert is ExpertRoute.STEM
    assert analysis.requires_history is False


async def test_router_deadline_returns_deterministic_fallback() -> None:
    settings = Settings(route_timeout_seconds=1.1)
    registry = build_model_registry(settings)
    router = RouterService(SlowStructuredGateway(), registry, settings)

    started = time.perf_counter()
    result = await router.route("Write a Python function to calculate a square root.")
    elapsed = time.perf_counter() - started

    assert elapsed < 2.0
    assert result.expert is ExpertRoute.CODING
    assert result.routing_fallback is True
    assert result.low_confidence is True
