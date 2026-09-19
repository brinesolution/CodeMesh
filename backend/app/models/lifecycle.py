import asyncio
import logging
import time

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

    async def prepare_specialist(self, model: str) -> float:
        async with self._lock:
            is_switch = self._active_specialist is not None and self._active_specialist != model
            started = time.perf_counter()
            if is_switch:
                try:
                    await self.gateway.unload(self._active_specialist)
                except Exception as exc:  # lifecycle cleanup must not break a request
                    logger.warning(
                        "model_unload_failed model=%s error=%s", self._active_specialist, exc
                    )
            self._active_specialist = model
            return round((time.perf_counter() - started) * 1000, 2) if is_switch else 0.0
