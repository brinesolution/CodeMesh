import pytest

from app.config import Settings
from app.models.ollama_client import OllamaClient
from app.models.registry import build_model_registry

pytestmark = pytest.mark.live


async def test_all_configured_models_are_installed() -> None:
    settings = Settings()
    client = OllamaClient(settings)
    health = await client.health()
    names = {model.name for model in health.models}
    required = {spec.model for spec in build_model_registry(settings).values()}

    assert health.reachable
    assert required <= names


@pytest.mark.parametrize("model_key", ["router", "conversation", "stem", "coding"])
async def test_each_configured_model_generates_short_response(model_key: str) -> None:
    settings = Settings()
    client = OllamaClient(settings)
    model = build_model_registry(settings)[model_key].model
    prompt = "Return one short sentence confirming local model connectivity."

    result = await client.generate(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        structured=model_key == "router",
    )

    assert result.model == model
    assert result.text.strip()

