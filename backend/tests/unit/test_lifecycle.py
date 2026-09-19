import pytest

from app.models.lifecycle import ModelLifecycle


class LifecycleGateway:
    def __init__(self) -> None:
        self.unloaded: list[str] = []

    async def unload(self, model: str) -> None:
        self.unloaded.append(model)


@pytest.mark.asyncio
async def test_lifecycle_reports_switch_and_releases_previous_specialist() -> None:
    gateway = LifecycleGateway()
    lifecycle = ModelLifecycle(gateway)

    first_switch_ms = await lifecycle.prepare_specialist("smollm2:1.7b")
    second_switch_ms = await lifecycle.prepare_specialist("qwen3:1.7b")

    assert first_switch_ms == 0.0
    assert second_switch_ms >= 0.0
    assert gateway.unloaded == ["smollm2:1.7b"]
