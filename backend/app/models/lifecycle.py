import asyncio
import logging

from app.models.gateway import ModelGateway

logger = logging.getLogger(__name__)


class ModelLifecycle:
    """Keep the router and at most one specialist intentionally resident."""

    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway
        self._active_specialist: str | None = None
        self._lock = asyncio.Lock()

    @property
    def active_specialist(self) -> str | None:
        return self._active_specialist

    async def prepare_specialist(self, model: str) -> None:
        async with self._lock:
            if self._active_specialist and self._active_specialist != model:
                try:
                    await self.gateway.unload(self._active_specialist)
                except Exception as exc:  # lifecycle cleanup must not break a request
                    logger.warning(
                        "model_unload_failed model=%s error=%s", self._active_specialist, exc
                    )
            self._active_specialist = model
