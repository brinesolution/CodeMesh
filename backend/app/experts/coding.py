from app.experts.base import ExpertDefinition

CODING_EXPERT = ExpertDefinition(
    key="coding",
    display_name="Coding Expert",
    model_key="coding",
    system_prompt=(
        "You are the CodeMesh Coding Expert. Handle software development, algorithms, debugging, "
        "databases, frontend/backend work, and code generation across common languages. Prefer "
        "correct, runnable, clearly formatted code. Explain only as much as needed."
    ),
    context_char_limit=24000,
    validator="code",
)

