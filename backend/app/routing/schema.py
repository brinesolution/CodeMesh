import json
import re
from enum import StrEnum

from pydantic import BaseModel, Field


class ExpertRoute(StrEnum):
    CONVERSATION = "conversation"
    STEM = "stem"
    CODING = "coding"


class RouteDecision(BaseModel):
    expert: ExpertRoute
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=160)


class RouteResult(RouteDecision):
    mode: str = "auto"
    router_model: str | None = None
    latency_ms: float | None = None
    routing_fallback: bool = False
    low_confidence: bool = False


def _clean_router_text(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()


def parse_route_output(text: str) -> RouteDecision:
    cleaned = _clean_router_text(text)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    candidates = [fenced.group(1)] if fenced else []
    candidates.append(cleaned)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
            return RouteDecision.model_validate(payload)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    raise ValueError("Router output did not contain a valid route decision.")


def deterministic_fallback(message: str) -> ExpertRoute:
    lowered = message.lower()
    coding_markers = (
        "write code",
        "implement",
        "debug",
        "refactor",
        "program",
        "algorithm",
        "python",
        "java",
        "javascript",
        "typescript",
        "sql",
        "html",
        "css",
        "react",
        "api",
        "function",
        "class ",
    )
    stem_markers = (
        "calculate",
        "solve",
        "equation",
        "force",
        "mass",
        "acceleration",
        "physics",
        "chemistry",
        "reaction rate",
        "integral",
        "derivative",
        "probability",
        "molar",
        "temperature",
    )
    if any(marker in lowered for marker in coding_markers):
        return ExpertRoute.CODING
    if any(marker in lowered for marker in stem_markers):
        return ExpertRoute.STEM
    return ExpertRoute.CONVERSATION
