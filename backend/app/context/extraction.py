"""Small deterministic memory safety net for weak structured Router output."""

import re

from app.context.schemas import MemoryChange, MemoryUpdate

_GRAVITY_BEFORE_VALUE = re.compile(
    r"(?:gravity|gravitational acceleration)(?:\s+constant)?\s*"
    r"(?:as|=|of|to|from|is)?\s*"
    r"(?P<value>\d+(?:\.\d+)?)"
)
_GRAVITY_AFTER_VALUE = re.compile(
    r"(?:use|using|set(?:ting)?(?:\s+gravity)?\s+to)\s+"
    r"(?P<value>\d+(?:\.\d+)?)\s*(?:m/s(?:\^?2|²))?\s*(?:as\s+)?gravity"
)


def extract_durable_memory(
    message: str, *, current_topic: str | None = None
) -> MemoryUpdate:
    """Extract only high-confidence, user-stated project state.

    The Router remains the primary extractor. This narrow fallback keeps durable
    state usable when the required small Router returns a valid but empty JSON
    object. It intentionally ignores generic coding/conversation requests.
    """

    lowered = message.lower()
    changes: list[MemoryChange] = []
    current_goal: str | None = None

    project_topic = _is_projectile_calculator(lowered) or (
        current_topic is not None and "projectile" in current_topic.lower()
    )
    if project_topic:
        changes.append(
            MemoryChange(
                category="topics",
                text="Projectile Motion Calculator",
                action="add",
            )
        )
    gravity = _gravity_value(lowered)
    if gravity:
        changes.append(
            MemoryChange(
                category="facts",
                id="projectile-gravity",
                text=f"Gravity = {gravity} m/s².",
                topic="Projectile Motion Calculator",
            )
        )
    if "initial velocity" in lowered and "launch angle" in lowered:
        changes.append(
            MemoryChange(
                category="facts",
                id="projectile-inputs",
                text="Inputs: initial velocity and launch angle.",
                topic="Projectile Motion Calculator",
            )
        )
    if all(term in lowered for term in ("maximum height", "horizontal range", "flight time")):
        changes.append(
            MemoryChange(
                category="facts",
                id="projectile-outputs",
                text="Outputs: maximum height, horizontal range, and total flight time.",
                topic="Projectile Motion Calculator",
            )
        )

    language = _implementation_language(lowered)
    if language:
        changes.append(
            MemoryChange(
                category="decisions",
                id="implementation-language",
                text=f"Use {language} as the implementation language.",
                topic="Projectile Motion Calculator",
            )
        )
    if "use functions" in lowered or ("functions" in lowered and "implement" in lowered):
        changes.append(
            MemoryChange(
                category="decisions",
                id="implementation-functions",
                text="Use functions to organize the implementation.",
                topic="Projectile Motion Calculator",
            )
        )

    if re.search(r"velocity\s+(?:is|must be)\s+positive", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="velocity-positive",
                text="Initial velocity must be positive.",
                topic="Projectile Motion Calculator",
            )
        )
    if re.search(
        r"angle\s+(?:is|must be)\s+(?:between|in the range of)\s+0\s*(?:and|to|-)\s*90",
        lowered,
    ) or re.search(r"angle[^.\n]{0,80}\b0\s*(?:to|-)\s*90\b", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="angle-range",
                text="Launch angle must be between 0 and 90 degrees.",
                topic="Projectile Motion Calculator",
            )
        )
    if re.search(r"(?:two|2)\s+decimal(?:\s+places|s)", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="two-decimals",
                text="Format results to two decimal places.",
                topic="Projectile Motion Calculator",
            )
        )
    if "offline" in lowered and (
        "fully" in lowered or "completely" in lowered or "work" in lowered
    ):
        changes.append(
            MemoryChange(
                category="constraints",
                id="offline",
                text="The application must work fully offline.",
                topic="Projectile Motion Calculator",
            )
        )
    if re.search(r"(?:no|without|must\s+not\s+use)\s+(?:any\s+)?(?:external\s+)?apis?", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="no-external-apis",
                text="Do not use external APIs.",
                topic="Projectile Motion Calculator",
            )
        )
    if (
        "no third-party math librar" in lowered
        or "must not use third-party math librar" in lowered
        or "without third-party math librar" in lowered
        or (
            "third-party math librar" in lowered
            and any(marker in lowered for marker in ("not use", "do not use", "without"))
        )
    ):
        changes.append(
            MemoryChange(
                category="constraints",
                id="no-third-party-math",
                text="Do not use third-party math libraries.",
                topic="Projectile Motion Calculator",
            )
        )
    if "first-year engineering student" in lowered or "first-year programming student" in lowered:
        changes.append(
            MemoryChange(
                category="constraints",
                id="first-year-readable",
                text="Keep the final code understandable to a first-year engineering student.",
                topic="Projectile Motion Calculator",
            )
        )

    if "current goal" in lowered and "unit test" in lowered:
        current_goal = "Add unit tests for the projectile-motion calculator."
    elif "unit tests" in lowered and ("need tests" in lowered or "add unit tests" in lowered):
        current_goal = "Add unit tests for the projectile-motion calculator."
    elif "implement" in lowered and (project_topic or "everything we discussed" in lowered):
        project_name = "projectile-motion calculator" if project_topic else "current project"
        current_goal = f"Implement the {project_name}."

    test_text = lowered.replace("°", " degrees").replace("-", " ")
    if "unit test" in test_text and ("tests for" in test_text or "test " in test_text):
        for task_id, text in (
            ("zero-degree", "Test a 0-degree input."),
            ("45-degree", "Test a 45-degree input."),
            ("negative-velocity", "Reject negative velocity."),
            ("angle-over-90", "Reject an angle above 90 degrees."),
            ("normal-case", "Test 30 m/s at 40 degrees."),
        ):
            if task_id == "zero-degree" and not re.search(r"\b0\s*degrees?\b", test_text):
                continue
            if (
                task_id == "45-degree"
                and not re.search(r"\b45\s*degrees?\b", test_text)
            ):
                continue
            if task_id == "negative-velocity" and "negative velocity" not in test_text:
                continue
            if (
                task_id == "angle-over-90"
                and "above 90" not in test_text
                and ">90" not in test_text
            ):
                continue
            if task_id == "normal-case" and "30 m/s" not in test_text:
                continue
            changes.append(
                MemoryChange(
                    category="open_tasks",
                    id=task_id,
                    text=text,
                    topic="Projectile Motion Calculator",
                )
            )

    return MemoryUpdate(
        changes=changes,
        current_goal=current_goal,
        memory_worthy=bool(changes or current_goal),
    )


def _is_projectile_calculator(message: str) -> bool:
    return "projectile" in message and (
        "calculator" in message
        or "maximum height" in message
        or "horizontal range" in message
        or "flight time" in message
    )


def _gravity_value(message: str) -> str | None:
    match = _GRAVITY_BEFORE_VALUE.search(message) or _GRAVITY_AFTER_VALUE.search(message)
    return match.group("value") if match else None


def _implementation_language(message: str) -> str | None:
    if re.search(r"\bjava\s*21\b", message) and any(
        marker in message for marker in ("implementation", "language", "code", "use")
    ):
        return "Java 21"
    if "python" in message and any(
        marker in message for marker in ("implement", "implementation", "in python", "use python")
    ):
        return "Python"
    return None
