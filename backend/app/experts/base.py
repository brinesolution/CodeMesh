from dataclasses import dataclass


@dataclass(frozen=True)
class ExpertDefinition:
    key: str
    display_name: str
    model_key: str
    system_prompt: str
    context_char_limit: int
    validator: str | None = None

