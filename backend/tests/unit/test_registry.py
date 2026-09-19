from app.config import Settings
from app.models.registry import build_model_registry


def test_model_registry_centralizes_required_stack() -> None:
    registry = build_model_registry(Settings())

    assert registry["router"].model == "qwen3:0.6b"
    assert registry["conversation"].model == "smollm2:1.7b"
    assert registry["stem"].model == "qwen3:1.7b"
    assert registry["coding"].model == "qwen2.5-coder:3b"


def test_model_registry_updates_one_role_and_restores_defaults() -> None:
    registry = build_model_registry(Settings())

    registry.assign_model("coding", "phi4-mini")

    assert registry.get_model("coding").model == "phi4-mini"
    assert registry.get_model("conversation").model == "smollm2:1.7b"
    registry.restore_defaults()
    assert registry.get_model("coding").model == "qwen2.5-coder:3b"
