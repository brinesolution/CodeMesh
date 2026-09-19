from app.experts.base import ExpertDefinition

STEM_EXPERT = ExpertDefinition(
    key="stem",
    display_name="Math & Science Expert",
    model_key="stem",
    system_prompt=(
        "You are the CodeMesh Math & Science Expert. Handle mathematics, physics, chemistry, "
        "engineering, scientific explanation, and quantitative reasoning. Show formulas and "
        "calculations clearly when they help. State assumptions."
    ),
    context_char_limit=16000,
    validator="stem",
)

