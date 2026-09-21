from app.context.schemas import SessionContextState

CONTEXT_ANALYSIS_SYSTEM_PROMPT = """You are the CodeMesh context analyst.
Return JSON only. Do not reveal private reasoning.
Decide whether the current request needs earlier conversation context and identify a compact topic.
Use relevant_memory_ids only for IDs supplied in the input.
"""

MEMORY_UPDATE_SYSTEM_PROMPT = """You are the CodeMesh memory extractor.
Return JSON only. Store only durable, user-visible facts, decisions, constraints, preferences,
goals, or open tasks. Ignore greetings, thanks, okay, and other trivial acknowledgements.
Use changes with category, action, text, id, or replaces. Never store hidden reasoning or secrets.
"""

SUMMARY_UPDATE_SYSTEM_PROMPT = """You are the CodeMesh session summarizer.
Return JSON only with a compact summary. Preserve important goals, decisions, constraints,
technology choices, topic progression, and outcomes. Do not write a transcript or hidden reasoning.
The supplied messages are only the newly unsummarized range; extend the existing summary
incrementally.
"""


def _memory_lines(state: SessionContextState) -> str:
    lines: list[str] = []
    for category in ("facts", "decisions", "constraints", "preferences", "open_tasks"):
        for item in getattr(state.memory, category):
            lines.append(f"{item.id} | {item.key or '-'} | {category} | {item.text}")
    if state.memory.current_goal:
        lines.append(f"current_goal | {state.memory.current_goal}")
    return "\n".join(lines) or "(none)"


def context_analysis_prompt(
    message: str, state: SessionContextState, recent_messages: list[dict[str, str]]
) -> str:
    recent = "\n".join(f"{item['role']}: {item['content']}" for item in recent_messages) or "(none)"
    return (
        "CURRENT REQUEST:\n"
        f"{message}\n\n"
        f"SESSION SUMMARY:\n{state.summary or '(none)'}\n\n"
        f"STRUCTURED MEMORY (id | category | text):\n{_memory_lines(state)}\n\n"
        f"RECENT CONVERSATION:\n{recent}\n\n"
        "Return this shape: {\"topic\":null,\"requires_history\":false,"
        "\"requires_summary\":false,\"reference_detected\":false,"
        "\"relevant_memory_ids\":[],\"recent_turns_needed\":0,\"memory_worthy\":false}"
    )


def memory_update_prompt(
    state: SessionContextState, user_message: str, assistant_message: str, source_message_id: int
) -> str:
    return (
        f"SOURCE USER MESSAGE ID: {source_message_id}\n"
        f"EXISTING MEMORY:\n{_memory_lines(state)}\n\n"
        f"USER:\n{user_message}\n\nASSISTANT:\n{assistant_message}\n\n"
        "Return {\"changes\":[],\"current_goal\":null,\"memory_worthy\":false}. "
        "For replacement, set action=update and use the existing item id."
    )


def summary_update_prompt(
    state: SessionContextState, messages: list[str], through_message_id: int
) -> str:
    joined = "\n".join(messages)
    return (
        f"SUMMARY THROUGH MESSAGE ID: {state.summary_through_message_id or 'none'}\n"
        f"EXISTING SUMMARY:\n{state.summary or '(none)'}\n\n"
        f"NEW UNSUMMARIZED RANGE THROUGH ID {through_message_id}:\n{joined}\n\n"
        "Return {\"summary\":\"compact summary\"}."
    )
