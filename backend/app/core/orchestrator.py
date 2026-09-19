import asyncio
import logging
from collections.abc import AsyncIterator

from app.config import Settings
from app.core.context_manager import ContextManager
from app.core.errors import CodeMeshError, GenerationCancelled
from app.experts.registry import get_expert
from app.models.gateway import ModelGateway
from app.models.lifecycle import ModelLifecycle
from app.models.registry import ModelRegistry
from app.persistence.repository import ChatRepository
from app.routing.schema import RouteResult
from app.routing.service import RouterService
from app.telemetry.system import system_snapshot
from app.telemetry.timing import Stopwatch
from app.validation.code import validate_python_response
from app.validation.stem import validate_stem_response

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        *,
        settings: Settings,
        gateway: ModelGateway,
        repository: ChatRepository,
        models: ModelRegistry,
        router: RouterService,
    ) -> None:
        self.settings = settings
        self.gateway = gateway
        self.repository = repository
        self.models = models
        self.router = router
        self.lifecycle = ModelLifecycle(gateway)
        self.context = ContextManager(repository, settings.context_turns)

    def ensure_session(self, session_id: str | None, mode: str) -> str:
        if session_id and self.repository.get_session(session_id):
            return session_id
        return self.repository.create_session(preferred_mode=mode).id

    def _route(self, message: str, mode: str) -> RouteResult:
        raise RuntimeError("Use async route selection")

    async def stream_chat(
        self, *, message: str, mode: str, session_id: str | None
    ) -> AsyncIterator[dict[str, object]]:
        if not message.strip():
            yield {
                "type": "error",
                "data": {"code": "EMPTY_MESSAGE", "message": "Message cannot be empty."},
            }
            return
        if len(message) > self.settings.max_prompt_chars:
            yield {
                "type": "error",
                "data": {
                    "code": "INPUT_TOO_LONG",
                    "message": "Message exceeds the local input limit.",
                },
            }
            return

        session_id = self.ensure_session(session_id, mode)
        self.repository.add_message(session_id, role="user", content=message)
        total_timer = Stopwatch()
        try:
            route = self.router.manual(mode) if mode != "auto" else await self.router.route(message)
            expert = get_expert(route.expert.value)
            expert_model = self.models.get_model(expert.model_key)
            yield {
                "type": "route",
                "data": {
                    "session_id": session_id,
                    **route.model_dump(mode="json"),
                    "expert_name": expert.display_name,
                    "expert_model": expert_model.model,
                    "expert_model_label": expert_model.label,
                },
            }
            yield {
                "type": "status",
                "data": {"state": "model_loading", "model": expert_model.model},
            }
            model_switch_latency = await self.lifecycle.prepare_specialist(expert_model.model)
            context = self.context.build_context(session_id, expert.context_char_limit)
            prompt_messages = [{"role": "system", "content": expert.system_prompt}, *context]
            prompt_messages.append({"role": "user", "content": message})
            yield {"type": "status", "data": {"state": "generating"}}
            generation_timer = Stopwatch()
            parts: list[str] = []
            async for chunk in self.gateway.stream(
                model=expert_model.model, messages=prompt_messages
            ):
                if chunk.text:
                    parts.append(chunk.text)
                    yield {"type": "token", "data": {"text": chunk.text}}
                if chunk.done:
                    break
            answer = "".join(parts).strip()
            validation = self._validate(route, message, answer)
            generation_latency = generation_timer.elapsed_ms()
            self.repository.add_message(
                session_id,
                role="assistant",
                content=answer,
                route=route.expert.value,
                model=expert_model.model,
                route_confidence=route.confidence,
                route_latency_ms=route.latency_ms,
                generation_latency_ms=generation_latency,
                validation_status=validation.status,
            )
            yield {"type": "validation", "data": validation.__dict__}
            health = await self.gateway.health()
            metrics = {
                "route_latency_ms": route.latency_ms,
                "model_switch_latency_ms": model_switch_latency,
                "generation_latency_ms": generation_latency,
                "total_latency_ms": total_timer.elapsed_ms(),
                "model": expert_model.model,
                "telemetry": system_snapshot(expert_model.model, health.reachable),
            }
            yield {"type": "metrics", "data": metrics}
            yield {
                "type": "done",
                "data": {
                    "session_id": session_id,
                    "message": answer,
                    "route": route.model_dump(mode="json"),
                    "model": expert_model.model,
                    "validation": validation.__dict__,
                    "metrics": metrics,
                },
            }
        except asyncio.CancelledError as exc:
            logger.info("generation_cancelled session_id=%s", session_id)
            raise GenerationCancelled("Generation stopped.") from exc
        except CodeMeshError as exc:
            logger.warning("request_failed code=%s", exc.code)
            yield {"type": "error", "data": {"code": exc.code, "message": str(exc)}}
        except Exception:
            logger.exception("request_failed code=INTERNAL_ERROR")
            yield {
                "type": "error",
                "data": {
                    "code": "INTERNAL_ERROR",
                    "message": "The local request could not be completed.",
                },
            }

    @staticmethod
    def _validate(route: RouteResult, prompt: str, answer: str):
        if route.expert.value == "coding":
            return validate_python_response(answer)
        if route.expert.value == "stem":
            return validate_stem_response(prompt, answer)
        from app.validation.base import ValidationResult

        return ValidationResult("none", "not_applicable", "No deterministic validator configured.")

    async def chat(self, *, message: str, mode: str, session_id: str | None) -> dict[str, object]:
        final: dict[str, object] | None = None
        async for event in self.stream_chat(message=message, mode=mode, session_id=session_id):
            if event["type"] == "done":
                final = event["data"]  # type: ignore[assignment]
            if event["type"] == "error":
                return {"error": event["data"]}
        return final or {"error": {"code": "NO_RESPONSE", "message": "No response was produced."}}
