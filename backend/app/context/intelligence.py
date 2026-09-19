import re
import time
from collections.abc import Callable

from app.config import Settings
from app.context.parsing import parse_json_object
from app.context.prompts import (
    CONTEXT_ANALYSIS_SYSTEM_PROMPT,
    MEMORY_UPDATE_SYSTEM_PROMPT,
    SUMMARY_UPDATE_SYSTEM_PROMPT,
    context_analysis_prompt,
    memory_update_prompt,
    summary_update_prompt,
)
from app.context.schemas import (
    ContextAnalysis,
    MemoryUpdate,
    SessionContextState,
    SummaryUpdate,
)
from app.models.gateway import ModelGateway
from app.models.registry import ModelRegistry
from app.routing.schema import deterministic_fallback


class ContextIntelligence:
    """Router-model operations for context decisions and derived memory."""

    def __init__(self, gateway: ModelGateway, models: ModelRegistry, settings: Settings) -> None:
        self.gateway = gateway
        self.models = models
        self.settings = settings

    async def analyze(
        self,
        message: str,
        state: SessionContextState,
        recent_messages: list[dict[str, str]],
    ) -> tuple[ContextAnalysis, float, str, bool]:
        model = self.models.get_model("router").model
        prompt = context_analysis_prompt(message, state, recent_messages)
        started = time.perf_counter()
        analysis = await self._structured(
            CONTEXT_ANALYSIS_SYSTEM_PROMPT,
            prompt,
            ContextAnalysis.model_validate,
        )
        if analysis is not None:
            return (
                _normalize_analysis(analysis, message, state, self.settings),
                round((time.perf_counter() - started) * 1000, 2),
                model,
                False,
            )
        fallback = _fallback_analysis(message, state, self.settings)
        return fallback, round((time.perf_counter() - started) * 1000, 2), model, True

    async def update_memory(
        self,
        state: SessionContextState,
        user_message: str,
        assistant_message: str,
        source_message_id: int,
    ) -> tuple[MemoryUpdate, float, str, bool]:
        model = self.models.get_model("router").model
        prompt = memory_update_prompt(state, user_message, assistant_message, source_message_id)
        started = time.perf_counter()
        update = await self._structured(
            MEMORY_UPDATE_SYSTEM_PROMPT,
            prompt,
            _parse_memory_update,
        )
        if update is not None:
            return update, round((time.perf_counter() - started) * 1000, 2), model, False
        return (
            MemoryUpdate(changes=[], memory_worthy=False),
            round((time.perf_counter() - started) * 1000, 2),
            model,
            True,
        )

    async def update_summary(
        self,
        state: SessionContextState,
        messages: list[str],
        through_message_id: int,
    ) -> tuple[SummaryUpdate, float, str, bool]:
        model = self.models.get_model("router").model
        prompt = summary_update_prompt(state, messages, through_message_id)
        started = time.perf_counter()
        update = await self._structured(
            SUMMARY_UPDATE_SYSTEM_PROMPT,
            prompt,
            SummaryUpdate.model_validate,
        )
        if update is not None:
            return update, round((time.perf_counter() - started) * 1000, 2), model, False
        return (
            SummaryUpdate(summary=state.summary),
            round((time.perf_counter() - started) * 1000, 2),
            model,
            True,
        )

    async def _structured(
        self,
        system_prompt: str,
        prompt: str,
        validator: Callable[[object], object],
    ) -> object | None:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        for attempt in range(2):
            try:
                result = await self.gateway.generate(
                    model=self.models.get_model("router").model,
                    messages=messages,
                    structured=True,
                )
                return validator(parse_json_object(result.text))
            except Exception:
                if attempt == 0:
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Return only one valid JSON object matching the requested shape."
                            ),
                        }
                    )
        return None


def _parse_memory_update(payload: object) -> MemoryUpdate:
    if not isinstance(payload, dict):
        raise ValueError("Memory update must be an object")
    if "changes" in payload:
        return MemoryUpdate.model_validate(payload)

    changes = []
    for action, values in (("add", payload.get("add")), ("update", payload.get("update"))):
        if isinstance(values, dict):
            values = [
                {"category": category, "text": text, "action": action}
                for category, texts in values.items()
                for text in (texts if isinstance(texts, list) else [texts])
            ]
        if isinstance(values, list):
            changes.extend(
                value
                if isinstance(value, dict)
                else {"category": "facts", "text": str(value), "action": action}
                for value in values
            )
    for value in payload.get("remove", []):
        if isinstance(value, str):
            changes.append({"category": "facts", "text": value, "action": "remove", "id": value})
    normalized = {**payload, "changes": changes}
    return MemoryUpdate.model_validate(normalized)


def _fallback_analysis(
    message: str, state: SessionContextState, settings: Settings
) -> ContextAnalysis:
    reference_detected = _has_context_reference(message)
    requires_history = reference_detected or bool(state.summary) or not state.memory.is_empty()
    return ContextAnalysis(
        expert=deterministic_fallback(message),
        confidence=0.35,
        topic=_infer_topic_from_request(message, state),
        requires_history=requires_history,
        requires_summary=requires_history and bool(state.summary),
        reference_detected=reference_detected,
        recent_turns_needed=settings.context_turns if requires_history else 0,
        memory_worthy=False,
    )


def _normalize_analysis(
    analysis: ContextAnalysis,
    message: str,
    state: SessionContextState,
    settings: Settings,
) -> ContextAnalysis:
    valid_memory_ids = {
        item.id
        for category in ("facts", "decisions", "constraints", "preferences", "open_tasks")
        for item in getattr(state.memory, category)
    }
    reference_detected = analysis.reference_detected or _has_context_reference(message)
    requires_history = (
        analysis.requires_history
        or bool(analysis.relevant_memory_ids)
        or reference_detected
    )
    requires_summary = analysis.requires_summary and bool(state.summary)
    recent_turns_needed = min(
        settings.context_turns,
        analysis.recent_turns_needed
        if analysis.recent_turns_needed > 0
        else settings.context_turns if requires_history else 0,
    )
    topic = analysis.topic.strip() if analysis.topic else None
    topic = topic or _infer_topic_from_request(message, state)
    return analysis.model_copy(
        update={
            "topic": topic or None,
            "reference_detected": reference_detected,
            "requires_history": requires_history,
            "requires_summary": requires_summary,
            "relevant_memory_ids": [
                item_id for item_id in analysis.relevant_memory_ids if item_id in valid_memory_ids
            ],
            "recent_turns_needed": recent_turns_needed,
        }
    )


def _has_context_reference(message: str) -> bool:
    return bool(
        re.search(
            r"\b(previous|earlier|before|same|that|those|it|continue|again|accordingly|"
            r"discussed|decided|go back|all three|this)\b",
            message.lower(),
        )
    )


def _infer_topic_from_request(message: str, state: SessionContextState) -> str | None:
    lowered = message.lower()
    if "projectile" in lowered and (
        "calculator" in lowered
        or "maximum height" in lowered
        or "horizontal range" in lowered
        or "flight time" in lowered
    ):
        return "Projectile Motion Calculator"
    return state.current_topic
