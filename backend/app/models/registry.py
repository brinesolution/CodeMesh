from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class ModelSpec:
    key: str
    model: str
    label: str
    role: str


class ModelRegistry(Mapping[str, ModelSpec]):
    """Runtime model assignments shared by routing, experts, and the API."""

    _ROLE_SETTINGS = {
        "router": ("router_model", "Qwen3 0.6B", "routing"),
        "conversation": ("chat_model", "SmolLM2 1.7B", "expert"),
        "stem": ("stem_model", "Qwen3 1.7B", "expert"),
        "coding": ("code_model", "Qwen2.5-Coder 3B", "expert"),
    }

    def __init__(self, settings: Settings) -> None:
        self._specs = {
            key: ModelSpec(
                key,
                getattr(settings, setting_name),
                _model_label(getattr(settings, setting_name), default_label),
                role,
            )
            for key, (setting_name, default_label, role) in self._ROLE_SETTINGS.items()
        }
        self._defaults = {key: spec.model for key, spec in self._specs.items()}

    def __getitem__(self, key: str) -> ModelSpec:
        return self._specs[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._specs)

    def __len__(self) -> int:
        return len(self._specs)

    def get_model(self, key: str) -> ModelSpec:
        return self[key]

    def assign_model(self, key: str, model: str) -> ModelSpec:
        current = self[key]
        updated = ModelSpec(current.key, model, _model_label(model, model), current.role)
        self._specs[key] = updated
        return updated

    def restore_defaults(self) -> None:
        for key, model in self._defaults.items():
            self.assign_model(key, model)

    def assignments(self) -> dict[str, str]:
        return {key: spec.model for key, spec in self._specs.items()}

    def defaults(self) -> dict[str, str]:
        return dict(self._defaults)


def _model_label(model: str, fallback: str) -> str:
    known_labels = {
        "qwen3:0.6b": "Qwen3 0.6B",
        "smollm2:1.7b": "SmolLM2 1.7B",
        "qwen3:1.7b": "Qwen3 1.7B",
        "qwen2.5-coder:3b": "Qwen2.5-Coder 3B",
    }
    return known_labels.get(model, fallback)


def build_model_registry(settings: Settings) -> ModelRegistry:
    return ModelRegistry(settings)
