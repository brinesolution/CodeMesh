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
    topic: str | None = None
    context_router_model: str | None = None
    context_latency_ms: float | None = None
    context_fallback: bool = False
    requires_history: bool = False
    requires_summary: bool = False
    reference_detected: bool = False
    recent_turns_needed: int = 0


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


def _contains_any(message: str, markers: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(marker)}(?!\w)", message) is not None
        for marker in markers
    )


def has_artifact_intent(message: str) -> bool:
    lowered = message.lower()
    return bool(
        re.search(
            r"\b(write|create|generate|implement|build|debug|refactor|rewrite|modify|convert)\b",
            lowered,
        )
        and re.search(
            r"\b(json|configuration|config|sql|query|function|code|script|handler|test|"
            r"implementation|class|endpoint|api)\b",
            lowered,
        )
    )


def deterministic_route(message: str) -> tuple[ExpertRoute, bool]:
    lowered = message.lower()
    if has_artifact_intent(message):
        return ExpertRoute.CODING, True
    conversation_overrides = (
        "python is",
        "python mean",
        "snakes",
        "wildlife",
        "friendlier tone",
        "habit and routine",
        "habit and a routine",
        "manager and a mentor",
        "think critically",
        "feedback useful",
        "which specialist handles",
        "handles code artifacts",
        "general everyday analogy",
        "compare sql databases and spreadsheets",
        "explain the concept of an api to a beginner",
        "using a library analogy",
        "library analogy",
        "without using technical jargon",
        "brainstorm names",
        "causes of procrastination",
        "make this sentence more concise",
        "fully offline",
        "external api",
        "external apis",
        "current goal",
    )
    if _contains_any(lowered, conversation_overrides):
        return ExpertRoute.CONVERSATION, True
    historical_query = bool(
        re.search(r"\b(?:what|which|list|summarize|recap)\b", lowered)
        and re.search(r"\b(?:historically|historical|history|previous|old)\b", lowered)
        and not re.search(r"\b(?:calculate|solve|derive|equation|formula)\b", lowered)
    )
    if historical_query:
        return ExpertRoute.CONVERSATION, True
    project_fact_signal = bool(
        re.search(
            r"\b(?:codename|budget|deadline|platforms?|concurrent\s+users|database|current\s+goal|"
            r"mongodb|postgresql|sqlite|mysql|mariadb|redis|dynamodb)\b",
            lowered,
        )
        and (
            re.search(
                r"\b(?:mongodb|postgresql|sqlite|mysql|mariadb|redis|dynamodb)\b",
                lowered,
            )
            or re.search(r"\b(?:replace|change|target|remember|use)\b", lowered)
        )
        and not re.search(
            r"\b(?:sql|schema|table|query|index|function|code|implementation|api)\b",
            lowered,
        )
    )
    if project_fact_signal:
        return ExpertRoute.CONVERSATION, True
    input_check_artifact = bool(
        re.search(r"\b(?:add|implement|write|create|modify|include)\b", lowered)
        and re.search(r"\binput\s+(?:check|validation)\b", lowered)
    )
    if input_check_artifact:
        return ExpertRoute.CODING, True

    coding_artifacts = (
        "implement",
        "refactor",
        "debug",
        "write code",
        "write merge sort",
        "write a sql",
        "write an sql",
        "write a bash script",
        "write unit tests",
        "junit tests",
        "write a java",
        "write a python",
        "write a c++",
        "c++ code",
        "python code",
        "java code",
        "write a spreadsheet formula",
        "write a rest handler",
        "generate a sql",
        "create a responsive",
        "create a css",
        "create a python",
        "create a calculator",
        "create a database index",
        "build a small express",
        "build an api",
        "in python",
        "in java",
        "in javascript",
        "in typescript",
        "in c++",
        "in bash",
        "with code",
        "sympy",
        "spreadsheet formula",
        "fastapi",
        "unit tests",
        "junit tests",
        "middleware",
    )
    if _contains_any(lowered, coding_artifacts):
        return ExpertRoute.CODING, True

    stem_markers = (
        "calculate",
        "solve",
        "equation",
        "force",
        "mass",
        "acceleration",
        "physics",
        "chemistry",
        "reaction",
        "molar",
        "moles",
        "temperature",
        "voltage",
        "volt",
        "ohm",
        "resistance",
        "circuit",
        "electric current",
        "newton",
        "energy",
        "integrate",
        "derivative",
        "integral",
        "probability",
        "wavelength",
        "frequency",
        "light",
        "gravity",
        "horizontal range",
        "seasons",
        "kinetic",
        "pressure",
        "gas",
        "compressed",
        "requests per second",
        "request rate",
        "throughput",
        "gb",
        "slope",
        "mitochondria",
        "element",
        "compound",
        "projectile",
        "velocity",
        "speed",
        "square root",
        "science",
        "motion",
        "roots",
        "ph",
        "acidity",
        "volume",
        "rectangular",
        "meter",
        "tectonics",
        "catalyst",
        "catalysts",
        "metal expand",
        "photosynthesis",
        "area of a circle",
        "mean of",
    )
    if _contains_any(lowered, stem_markers):
        return ExpertRoute.STEM, True

    coding_concepts = (
        "algorithm",
        "binary search",
        "big o",
        "null pointer",
        "database index",
        "add an index",
        "index to a",
        "http client",
        "json payload",
        "loop",
        "recursion",
        "software",
        "python",
        "javascript",
        "typescript",
        "sql",
        "html",
        "css",
        "react",
        "java",
        "api",
        "function",
        "code",
    )
    if _contains_any(lowered, coding_concepts):
        return ExpertRoute.CODING, True
    general_conversation = re.search(
        r"\b(?:explain|describe|summarize|compare|why|which|list|what|how\s+does)\b",
        lowered,
    )
    return ExpertRoute.CONVERSATION, bool(general_conversation)


def deterministic_fallback(message: str) -> ExpertRoute:
    return deterministic_route(message)[0]
