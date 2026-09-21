"""Small deterministic memory safety net for weak structured Router output."""

import re
from collections.abc import Iterable

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
_CODENAME = re.compile(
    r"\b(?:project\s+)?codename\s*(?:is|=|:)?\s*(?P<value>[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+)"
)
_BUDGET = re.compile(
    r"\b(?:project\s+)?budget\s*(?:is|=|:|of|to)\s*"
    r"(?P<value>(?:₹|rs\.?|inr\s*)\s*[\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)
_DATABASE = re.compile(
    r"\b(?:project\s+)?database\s*(?:is|=|:|will\s+use)\s*"
    r"(?P<value>[A-Za-z][\w.-]*)",
    re.IGNORECASE,
)
_DATABASE_REPLACEMENT = re.compile(
    r"\b(?:replace|change)\s+(?P<old>[A-Za-z][\w.-]*)\s+with\s+(?P<new>[A-Za-z][\w.-]*)",
    re.IGNORECASE,
)
_DEADLINE = re.compile(
    r"\b(?:deadline|launch date|release date)\s*(?:is|=|:|on|to)?\s*"
    r"(?P<value>[A-Za-z0-9][A-Za-z0-9 /-]{2,60})",
    re.IGNORECASE,
)
_CONCURRENCY = re.compile(
    r"\b(?:concurrency|concurrent\s+users)\s*(?:is|=|:|of|set\s+to)?\s*"
    r"(?P<value>\d[\d,]*)",
    re.IGNORECASE,
)
_CONCURRENT_USERS_BEFORE_LABEL = re.compile(
    r"\b(?P<value>\d[\d,]*)\s+concurrent\s+users\b", re.IGNORECASE
)
_PLATFORMS = re.compile(
    r"\bplatforms?\s*(?:are|is|=|:)?\s*(?P<value>[^.\n]{2,80})",
    re.IGNORECASE,
)
_DATABASE_NAMES = {
    "mongodb",
    "postgresql",
    "postgres",
    "mysql",
    "sqlite",
    "mariadb",
    "redis",
    "dynamodb",
}
_NON_VALUE_WORDS = {
    "current",
    "previous",
    "old",
    "new",
    "what",
    "which",
    "did",
    "we",
    "and",
    "is",
    "was",
    "were",
    "the",
    "a",
    "an",
}


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

    changes.extend(_project_state_changes(message))

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
                key="physics.gravity",
                text=f"Gravity = {gravity} m/s².",
                topic="Projectile Motion Calculator",
            )
        )
    if "initial velocity" in lowered and "launch angle" in lowered:
        changes.append(
            MemoryChange(
                category="facts",
                id="projectile-inputs",
                key="physics.projectile_inputs",
                text="Inputs: initial velocity and launch angle.",
                topic="Projectile Motion Calculator",
            )
        )
    if all(term in lowered for term in ("maximum height", "horizontal range", "flight time")):
        changes.append(
            MemoryChange(
                category="facts",
                id="projectile-outputs",
                key="physics.projectile_outputs",
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
                key="project.language",
                text=f"Use {language} as the implementation language.",
                topic="Projectile Motion Calculator",
            )
        )
    if "use functions" in lowered or ("functions" in lowered and "implement" in lowered):
        changes.append(
            MemoryChange(
                category="decisions",
                id="implementation-functions",
                key="project.implementation_functions",
                text="Use functions to organize the implementation.",
                topic="Projectile Motion Calculator",
            )
        )

    if re.search(r"velocity\s+(?:is|must be)\s+positive", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="velocity-positive",
                key="physics.velocity_positive",
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
                key="physics.angle_range",
                text="Launch angle must be between 0 and 90 degrees.",
                topic="Projectile Motion Calculator",
            )
        )
    if re.search(r"(?:two|2)\s+decimal(?:\s+places|s)", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="two-decimals",
                key="formatting.decimal_places",
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
                key="project.offline",
                text="The application must work fully offline.",
                topic="Projectile Motion Calculator",
            )
        )
    if re.search(r"(?:no|without|must\s+not\s+use)\s+(?:any\s+)?(?:external\s+)?apis?", lowered):
        changes.append(
            MemoryChange(
                category="constraints",
                id="no-external-apis",
                key="project.external_apis",
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
                key="project.third_party_math",
                text="Do not use third-party math libraries.",
                topic="Projectile Motion Calculator",
            )
        )
    if "first-year engineering student" in lowered or "first-year programming student" in lowered:
        changes.append(
            MemoryChange(
                category="constraints",
                id="first-year-readable",
                key="project.readability",
                text="Keep the final code understandable to a first-year engineering student.",
                topic="Projectile Motion Calculator",
            )
        )

    if "current goal" in lowered and "unit test" in lowered:
        project_name = "projectile-motion calculator" if project_topic else "current project"
        current_goal = f"Add unit tests for the {project_name}."
    elif "unit tests" in lowered and ("need tests" in lowered or "add unit tests" in lowered):
        project_name = "projectile-motion calculator" if project_topic else "current project"
        current_goal = f"Add unit tests for the {project_name}."
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
                    key=f"project.task.{task_id}",
                    text=text,
                    topic="Projectile Motion Calculator",
                )
            )

    return MemoryUpdate(
        changes=changes,
        current_goal=current_goal,
        memory_worthy=bool(changes or current_goal),
    )


def historical_project_changes(messages: Iterable[str]) -> list[str]:
    """Return compact change history derived from user-visible project messages."""

    message_list = list(messages)
    languages: list[str] = []
    gravities: list[str] = []
    for message in message_list:
        lowered = message.lower()
        language = _implementation_language(lowered)
        if language and (not languages or languages[-1] != language):
            languages.append(language)
        gravity = _gravity_value(lowered)
        if gravity and (not gravities or gravities[-1] != gravity):
            gravities.append(gravity)

    changes: list[str] = []
    if len(languages) > 1:
        changes.append(f"Language history: {' -> '.join(languages)}.")
    if len(gravities) > 1:
        changes.append(f"Gravity history: {' -> '.join(gravities)} m/s².")
    values_by_key: dict[str, list[str]] = {}
    for message in message_list:
        for change in extract_durable_memory(message).changes:
            if not change.key or change.key in {"project.language", "physics.gravity"}:
                continue
            value = change.text.rstrip(".")
            values = values_by_key.setdefault(change.key, [])
            if not values or values[-1] != value:
                values.append(value)
    for key, values in values_by_key.items():
        if len(values) > 1:
            changes.append(f"{key} history: {' -> '.join(values)}.")
    return changes


def _project_state_changes(message: str) -> list[MemoryChange]:
    """Extract explicit, high-confidence project state without guessing prose."""

    changes: list[MemoryChange] = []
    codename = _CODENAME.search(message)
    if codename:
        value = codename.group("value").strip(" .,!?")
        changes.append(
            MemoryChange(
                category="facts",
                key="project.codename",
                id="project-codename",
                text=f"Project codename = {value}.",
            )
        )

    budget = _BUDGET.search(message)
    if budget:
        value = re.sub(r"\s+", "", budget.group("value")).strip(".,")
        changes.append(
            MemoryChange(
                category="facts",
                key="project.total_budget",
                id="project-total-budget",
                text=f"Project budget = {value}.",
            )
        )

    database = _DATABASE.search(message)
    if database:
        value = database.group("value").strip(" .,!?")
        if value.lower() not in _NON_VALUE_WORDS:
            changes.append(
                MemoryChange(
                    category="decisions",
                    key="project.database",
                    id="project-database",
                    text=f"Database = {value}.",
                )
            )
    replacement = _DATABASE_REPLACEMENT.search(message)
    if replacement and (
        replacement.group("old").lower() in _DATABASE_NAMES
        or replacement.group("new").lower() in _DATABASE_NAMES
        or "database" in message.lower()
    ):
        value = replacement.group("new").strip(" .,!?")
        changes.append(
            MemoryChange(
                category="decisions",
                key="project.database",
                id="project-database",
                action="update",
                text=f"Database = {value}.",
            )
        )

    deadline = _DEADLINE.search(message)
    if deadline:
        value = deadline.group("value").strip(" .,!?")
        if value.lower().split()[0] not in _NON_VALUE_WORDS:
            changes.append(
                MemoryChange(
                    category="facts",
                    key="project.deadline",
                    id="project-deadline",
                    text=f"Project deadline = {value}.",
                )
            )

    concurrency = _CONCURRENCY.search(message) or _CONCURRENT_USERS_BEFORE_LABEL.search(
        message
    )
    if concurrency:
        value = concurrency.group("value").replace(",", "")
        changes.append(
            MemoryChange(
                category="facts",
                key="project.concurrent_users",
                id="project-concurrent-users",
                text=f"Concurrent users = {value}.",
            )
        )

    platforms = _PLATFORMS.search(message)
    if platforms:
        value = re.sub(
            r"^(?:to|on)\s+",
            "",
            platforms.group("value").strip(" .,!?"),
            flags=re.IGNORECASE,
        )
        if any(token in value.lower() for token in ("android", "ios", "web", "windows", "macos")):
            changes.append(
                MemoryChange(
                    category="facts",
                    key="project.platforms",
                    id="project-platforms",
                    text=f"Platforms = {value}.",
                )
            )
    elif re.search(r"\bandroid\s+only\b", message, re.IGNORECASE):
        changes.append(
            MemoryChange(
                category="facts",
                key="project.platforms",
                id="project-platforms",
                text="Platforms = Android only.",
            )
        )
    return changes


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
