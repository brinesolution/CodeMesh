from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

try:
    from .semantic_checks import percentile
except ImportError:
    from semantic_checks import percentile

import httpx

PROMPTS = {
    "conversation": "Explain cloud computing in two sentences.",
    "stem": "A 5 kg mass has a force of 20 N. Find acceleration.",
    "coding": "Write a Python function that returns the larger of two integers.",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure local CodeMesh route and specialist latency."
    )
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--output", default="evaluation/reports/latency_phase15.json")
    args = parser.parse_args()
    measurements: list[dict[str, object]] = []
    with httpx.Client(base_url=args.api, timeout=240.0) as client:
        for round_number in range(1, args.rounds + 1):
            for expert, prompt in PROMPTS.items():
                before = client.get("/api/v1/system").json()
                started = time.perf_counter()
                response = client.post("/api/v1/chat", json={"message": prompt, "mode": expert})
                elapsed = round((time.perf_counter() - started) * 1000, 2)
                response.raise_for_status()
                payload = response.json()
                after = client.get("/api/v1/system").json()
                measurements.append(
                    {
                        "round": round_number,
                        "expert": expert,
                        "elapsed_ms": elapsed,
                        "route": payload.get("route"),
                        "metrics": payload.get("metrics"),
                        "before": before,
                        "after": after,
                    }
                )
                print(f"round {round_number} {expert}: {elapsed:.0f} ms")
    grouped = {
        expert: [float(row["elapsed_ms"]) for row in measurements if row["expert"] == expert]
        for expert in PROMPTS
    }
    metric_values = {
        name: [float(row["metrics"].get(name) or 0) for row in measurements if row.get("metrics")]
        for name in (
            "route_latency_ms",
            "generation_latency_ms",
            "model_switch_latency_ms",
            "total_latency_ms",
        )
    }
    snapshots = [row["after"] for row in measurements if row.get("after")]
    report = {
        "measurements": measurements,
        "summary": {
            expert: {
                "count": len(values),
                "mean_ms": round(statistics.mean(values), 2),
                "min_ms": round(min(values), 2),
                "max_ms": round(max(values), 2),
                "p50_ms": percentile(values, 0.50),
                "p90_ms": percentile(values, 0.90),
            }
            for expert, values in grouped.items()
        },
        "metric_summary": {
            name: {
                "count": len(values),
                "p50_ms": percentile(values, 0.50),
                "p90_ms": percentile(values, 0.90),
                "max_ms": round(max(values), 2) if values else 0,
            }
            for name, values in metric_values.items()
        },
        "resource_observations": {
            "ram_used_bytes_max": max(
                (snapshot.get("ram_used_bytes") or 0 for snapshot in snapshots),
                default=0,
            ),
            "vram_used_bytes_max": max(
                (snapshot.get("vram_used_bytes") or 0 for snapshot in snapshots),
                default=0,
            ),
            "gpu_utilization_percent_max": max(
                (snapshot.get("gpu_utilization_percent") or 0 for snapshot in snapshots),
                default=0,
            ),
            "active_models_observed": sorted(
                {
                    snapshot.get("active_model")
                    for snapshot in snapshots
                    if snapshot.get("active_model")
                }
            ),
        },
        "timeout_observations": {
            "over_10_seconds": sum(float(row["elapsed_ms"]) > 10000 for row in measurements),
            "over_30_seconds": sum(float(row["elapsed_ms"]) > 30000 for row in measurements),
            "over_120_seconds": sum(float(row["elapsed_ms"]) > 120000 for row in measurements),
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
