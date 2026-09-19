from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class ModelSpec:
    key: str
    model: str
    label: str
    role: str


def build_model_registry(settings: Settings) -> dict[str, ModelSpec]:
    return {
        "router": ModelSpec("router", settings.router_model, "Qwen3 0.6B", "routing"),
        "conversation": ModelSpec(
            "conversation", settings.chat_model, "SmolLM2 1.7B", "expert"
        ),
        "stem": ModelSpec("stem", settings.stem_model, "Qwen3 1.7B", "expert"),
        "coding": ModelSpec(
            "coding", settings.code_model, "Qwen2.5-Coder 3B", "expert"
        ),
    }

