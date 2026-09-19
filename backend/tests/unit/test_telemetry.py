import sys
import types

from app.telemetry.system import system_snapshot


def test_gpu_telemetry_failure_degrades_without_breaking(monkeypatch) -> None:
    failing_nvml = types.SimpleNamespace(
        nvmlInit=lambda: (_ for _ in ()).throw(RuntimeError("no GPU"))
    )
    monkeypatch.setitem(sys.modules, "pynvml", failing_nvml)

    snapshot = system_snapshot(active_model="smollm2:1.7b", ollama_reachable=True)

    assert snapshot["active_model"] == "smollm2:1.7b"
    assert snapshot["telemetry_available"] is False
    assert snapshot["ram_total_bytes"]
