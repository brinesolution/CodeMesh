from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

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
    parser.add_argument("--output", default="evaluation/reports/latency_latest.json")
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
    report = {
        "measurements": measurements,
        "summary": {
            expert: {
                "count": len(values),
                "mean_ms": round(statistics.mean(values), 2),
                "min_ms": round(min(values), 2),
                "max_ms": round(max(values), 2),
            }
            for expert, values in grouped.items()
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
