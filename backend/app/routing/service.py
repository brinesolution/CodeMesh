import time

from app.config import Settings
from app.core.errors import RouterFailure
from app.models.gateway import ModelGateway
from app.models.registry import ModelRegistry, ModelSpec
from app.routing.prompt import ROUTER_SYSTEM_PROMPT
from app.routing.schema import (
    ExpertRoute,
    RouteDecision,
    RouteResult,
    deterministic_fallback,
    deterministic_route,
    parse_route_output,
)


class RouterService:
    def __init__(
        self,
        gateway: ModelGateway,
        router: ModelSpec | ModelRegistry,
        settings: Settings,
    ) -> None:
        self.gateway = gateway
        self._models = router if isinstance(router, ModelRegistry) else None
        self._router_spec = router if isinstance(router, ModelSpec) else None
        self.settings = settings

    def _current_router(self) -> ModelSpec:
        if self._models is not None:
            return self._models.get_model("router")
        assert self._router_spec is not None
        return self._router_spec

    async def route(self, message: str) -> RouteResult:
        started = time.perf_counter()
        router_model = self._current_router().model
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
        decision: RouteDecision | None = None
        for attempt in range(2):
            try:
                result = await self.gateway.generate(
                    model=router_model, messages=messages, structured=True
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
                        router_model=router_model,
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
        guardrail_route, guardrail_used = deterministic_route(message)
        guardrail_changed = guardrail_used and guardrail_route is not decision.expert
        if guardrail_changed:
            decision = decision.model_copy(
                update={
                    "expert": guardrail_route,
                    "confidence": 0.65,
                    "reason": (
                        "Deterministic domain guardrail resolved the router/model disagreement."
                    ),
                }
            )
        return RouteResult(
            **decision.model_dump(),
            mode="auto",
            router_model=router_model,
            latency_ms=round(elapsed, 2),
            routing_fallback=guardrail_changed,
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
