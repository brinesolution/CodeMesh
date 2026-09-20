import asyncio
import logging
from collections.abc import AsyncIterator

from app.config import Settings
from app.context.intelligence import ContextIntelligence
from app.context.schemas import ContextAnalysis
from app.context.service import ContextMemoryService
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
        context_intelligence: ContextIntelligence | None = None,
    ) -> None:
        self.settings = settings
        self.gateway = gateway
        self.repository = repository
        self.models = models
        self.router = router
        self.context_memory = ContextMemoryService(repository, settings)
        self.context_intelligence = context_intelligence or ContextIntelligence(
            gateway, models, settings
        )
        self.lifecycle = ModelLifecycle(gateway)
        self.context = ContextManager(
            repository,
            settings.context_turns,
            settings=settings,
            memory_service=self.context_memory,
        )

    def ensure_session(self, session_id: str | None, mode: str) -> str:
        if session_id and self.repository.get_session(session_id):
            return session_id
        return self.repository.create_session(preferred_mode=mode).id

    async def rebuild_context(self, session_id: str) -> dict[str, object]:
        """Rebuild derived context from durable raw messages without rewriting them."""
        if self.repository.get_session(session_id) is None:
            raise ValueError("Session not found")
        self.context_memory.reset(session_id)
        messages = self.repository.all_messages(session_id)
        for index, message in enumerate(messages):
            if message.role != "user":
                continue
            state = self.context_memory.get(session_id)
            recent = [
                {"role": item.role, "content": item.content}
                for item in messages[max(0, index - self.settings.context_turns * 2) : index]
            ]
            analysis, _, router_model, _ = await self.context_intelligence.analyze(
                message.content, state, recent
            )
            self.context_memory.record_analysis(session_id, analysis, router_model)
            if index + 1 >= len(messages) or messages[index + 1].role != "assistant":
                continue
            assistant = messages[index + 1]
            if ContextMemoryService.is_trivial(message.content):
                continue
            state = self.context_memory.get(session_id)
            update, _, memory_model, _ = await self.context_intelligence.update_memory(
                state, message.content, assistant.content, message.id
            )
            self.context_memory.apply_memory_update(
                session_id,
                update,
                source_message_id=message.id,
                router_model=memory_model,
                source_text=message.content,
            )

        while True:
            batch = self.context_memory.summary_batch(session_id)
            if batch is None:
                break
            state = self.context_memory.get(session_id)
            update, _, summary_model, _ = await self.context_intelligence.update_summary(
                state,
                [f"{item.role}: {item.content}" for item in batch.messages],
                batch.through_message_id,
            )
            self.context_memory.apply_summary_update(
                session_id,
                update,
                through_message_id=batch.through_message_id,
                router_model=summary_model,
            )
        return self.context_memory.context_view(session_id) or {}

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
        user_message = self.repository.add_message(session_id, role="user", content=message)
        total_timer = Stopwatch()
        try:
            route = self.router.manual(mode) if mode != "auto" else await self.router.route(message)
            analysis, context_latency, context_model, context_fallback = (
                await self._analyze_context(session_id, message)
            )
            self.context_memory.record_analysis(session_id, analysis, context_model)
            route = route.model_copy(
                update={
                    "topic": analysis.topic,
                    "context_router_model": context_model,
                    "context_latency_ms": context_latency,
                    "context_fallback": context_fallback,
                    "requires_history": analysis.requires_history,
                    "requires_summary": analysis.requires_summary,
                    "reference_detected": analysis.reference_detected,
                    "recent_turns_needed": analysis.recent_turns_needed,
                }
            )
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
            context_package = self.context.build_specialist_context(
                session_id, expert.context_char_limit, message, analysis
            )
            context_state_snapshot = self.context_memory.get(session_id)
            prompt_messages = context_package.to_messages(expert.system_prompt)
            context_metadata = {
                "session_id": session_id,
                "mode": route.mode,
                "expert": route.expert.value,
                "router_model": context_model,
                "specialist_model": expert_model.model,
                "recent_message_count": len(context_package.recent_messages),
                "recent_message_roles": [
                    item["role"] for item in context_package.recent_messages
                ],
                "summary_included": bool(context_package.summary),
                "structured_memory_included": bool(context_package.relevant_memory),
                "memory_item_count": len(context_package.relevant_memory),
                "current_goal_included": bool(context_package.current_goal),
                "historical_changes_included": bool(context_package.historical_changes),
                "context_analysis": {
                    "topic": analysis.topic,
                    "requires_history": analysis.requires_history,
                    "requires_summary": analysis.requires_summary,
                    "reference_detected": analysis.reference_detected,
                    "recent_turns_needed": analysis.recent_turns_needed,
                },
                "route_confidence": route.confidence,
                "context_analysis_latency_ms": context_latency,
            }
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
            assistant_message = self.repository.add_message(
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
            maintenance = await self._maintain_context(
                session_id, message, answer, user_message.id
            )
            context_run = self.repository.add_context_run(
                session_id,
                current_message_id=user_message.id,
                response_message_id=assistant_message.id,
                expert=route.expert.value,
                model=expert_model.model,
                router_model=context_model,
                summary_included=bool(context_package.summary),
                memory_ids=[item.id for item in context_package.relevant_memory],
                recent_message_ids=context_package.recent_message_ids,
                approx_context_size=sum(len(item["content"]) for item in prompt_messages),
                context_analysis={
                    **context_metadata,
                    "current_goal_included": bool(context_package.current_goal),
                    "historical_changes_included": bool(context_package.historical_changes),
                    "summary_updated": maintenance["summary_update_status"] == "updated",
                    "summary_text_snapshot": context_package.summary,
                    "summary_through_message_id_snapshot": (
                        context_state_snapshot.summary_through_message_id
                    ),
                    "memory_items_snapshot": [
                        item.model_dump(mode="json")
                        for item in context_package.relevant_memory
                    ],
                    "current_goal_snapshot": context_package.current_goal,
                },
            )
            yield {"type": "validation", "data": validation.__dict__}
            health = await self.gateway.health()
            metrics = {
                "route_latency_ms": route.latency_ms,
                "model_switch_latency_ms": model_switch_latency,
                "generation_latency_ms": generation_latency,
                "specialist_generation_latency_ms": generation_latency,
                "routing_context_latency_ms": (route.latency_ms or 0)
                + (route.context_latency_ms or 0),
                "memory_update_latency_ms": maintenance["memory_update_latency_ms"],
                "summary_update_latency_ms": maintenance["summary_update_latency_ms"],
                "total_latency_ms": total_timer.elapsed_ms(),
                "model": expert_model.model,
                "context": {
                    **context_metadata,
                    "context_run_id": context_run.id if context_run else None,
                    "memory_update_status": maintenance["memory_update_status"],
                    "summary_update_status": maintenance["summary_update_status"],
                    "memory_model": maintenance["memory_model"],
                    "summary_model": maintenance["summary_model"],
                },
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

    async def _analyze_context(
        self, session_id: str, message: str
    ) -> tuple[ContextAnalysis, float, str, bool]:
        state = self.context_memory.get(session_id)
        if ContextMemoryService.is_trivial(message):
            analysis = ContextAnalysis(
                requires_history=bool(state.summary or not state.memory.is_empty()),
                requires_summary=bool(state.summary),
                recent_turns_needed=self.settings.context_turns
                if state.summary or not state.memory.is_empty()
                else 0,
            )
            return analysis, 0.0, self.models.get_model("router").model, False
        recent = [
            {"role": item.role, "content": item.content}
            for item in self.repository.recent_messages(
                session_id, min(self.settings.context_turns * 2, 6)
            )
        ]
        if (
            recent
            and recent[-1]["role"] == "user"
            and recent[-1]["content"].strip() == message.strip()
        ):
            recent = recent[:-1]
        return await self.context_intelligence.analyze(message, state, recent)

    async def _maintain_context(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        source_message_id: int,
    ) -> dict[str, object]:
        memory_latency = 0.0
        summary_latency = 0.0
        memory_status = "skipped"
        summary_status = "not_due"
        memory_model: str | None = None
        summary_model: str | None = None
        if not ContextMemoryService.is_trivial(user_message):
            try:
                state = self.context_memory.get(session_id)
                update, memory_latency, model, fallback = (
                    await self.context_intelligence.update_memory(
                        state, user_message, assistant_message, source_message_id
                    )
                )
                memory_model = model
                saved_state = self.context_memory.apply_memory_update(
                    session_id,
                    update,
                    source_message_id=source_message_id,
                    router_model=model,
                    source_text=user_message,
                )
                if saved_state.version > state.version:
                    memory_status = (
                        "safety_net" if fallback or not update.memory_worthy else "updated"
                    )
                else:
                    memory_status = "empty"
            except Exception:
                memory_status = "failed"
                logger.debug("memory_update_failed session_id=%s", session_id, exc_info=True)

        try:
            batch = self.context_memory.summary_batch(session_id)
        except Exception:
            logger.debug("summary_batch_failed session_id=%s", session_id, exc_info=True)
            batch = None
        if batch is not None:
            try:
                state = self.context_memory.get(session_id)
                update, summary_latency, model, fallback = (
                    await self.context_intelligence.update_summary(
                        state,
                        [f"{item.role}: {item.content}" for item in batch.messages],
                        batch.through_message_id,
                    )
                )
                summary_model = model
                self.context_memory.apply_summary_update(
                    session_id,
                    update,
                    through_message_id=batch.through_message_id,
                    router_model=model,
                )
                summary_status = "fallback" if fallback else "updated"
            except Exception:
                summary_status = "failed"
                logger.debug("summary_update_failed session_id=%s", session_id, exc_info=True)
        return {
            "memory_update_latency_ms": memory_latency,
            "summary_update_latency_ms": summary_latency,
            "memory_update_status": memory_status,
            "summary_update_status": summary_status,
            "memory_model": memory_model,
            "summary_model": summary_model,
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
