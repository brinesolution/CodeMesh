import logging
import time

import psutil

logger = logging.getLogger(__name__)
STARTED_AT = time.time()


def _gpu_snapshot() -> dict[str, object | None]:
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode("utf-8", errors="replace")
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return {
            "gpu_name": name,
            "gpu_utilization_percent": float(utilization.gpu),
            "vram_used_bytes": int(memory.used),
            "vram_total_bytes": int(memory.total),
            "telemetry_available": True,
        }
    except Exception as exc:
        logger.debug("gpu_telemetry_unavailable error=%s", exc)
        return {
            "gpu_name": None,
            "gpu_utilization_percent": None,
            "vram_used_bytes": None,
            "vram_total_bytes": None,
            "telemetry_available": False,
        }


def system_snapshot(
    active_model: str | None = None, ollama_reachable: bool | None = None
) -> dict[str, object | None]:
    memory = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_used_bytes": int(memory.used),
        "ram_total_bytes": int(memory.total),
        "backend_uptime_seconds": round(time.time() - STARTED_AT, 2),
        "active_model": active_model,
        "ollama_reachable": ollama_reachable,
        **_gpu_snapshot(),
    }
