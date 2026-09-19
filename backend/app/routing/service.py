import time

from app.config import Settings
from app.core.errors import RouterFailure
from app.models.gateway import ModelGateway
from app.models.registry import ModelSpec
from app.routing.prompt import ROUTER_SYSTEM_PROMPT
from app.routing.schema import (
    ExpertRoute,
    RouteDecision,
    RouteResult,
    deterministic_fallback,
    parse_route_output,
)


class RouterService:
    def __init__(self, gateway: ModelGateway, router_spec: ModelSpec, settings: Settings) -> None:
        self.gateway = gateway
        self.router_spec = router_spec
        self.settings = settings

    async def route(self, message: str) -> RouteResult:
        started = time.perf_counter()
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
        decision: RouteDecision | None = None
        for attempt in range(2):
            try:
                result = await self.gateway.generate(
                    model=self.router_spec.model, messages=messages, structured=True
                )
                decision = parse_route_output(result.text)
                break
            except Exception as exc:
                if attempt == 1:
                    fallback = deterministic_fallback(message)
                    elapsed = (time.perf_counter() - started) * 1000
                    return RouteResult(
                        mode="auto",
                        expert=fallback,
                        confidence=0.35,
                        reason="Deterministic fallback used after router output failure.",
                        router_model=self.router_spec.model,
                        latency_ms=round(elapsed, 2),
                        routing_fallback=True,
                        low_confidence=True,
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": "Return only valid JSON with expert, confidence, and reason.",
                    }
                )
                _ = exc
        if decision is None:
            raise RouterFailure("Router did not produce a route decision.")
        elapsed = (time.perf_counter() - started) * 1000
        return RouteResult(
            **decision.model_dump(),
            mode="auto",
            router_model=self.router_spec.model,
            latency_ms=round(elapsed, 2),
            low_confidence=decision.confidence < self.settings.router_confidence_threshold,
        )

    def manual(self, mode: str) -> RouteResult:
        mapping = {
            "conversation": ExpertRoute.CONVERSATION,
            "stem": ExpertRoute.STEM,
            "coding": ExpertRoute.CODING,
        }
        if mode not in mapping:
            raise ValueError(f"Unsupported manual mode: {mode}")
        return RouteResult(
            mode=mode,
            expert=mapping[mode],
            confidence=1.0,
            reason="Manual expert selected by the user.",
            router_model=None,
            latency_ms=0.0,
        )

