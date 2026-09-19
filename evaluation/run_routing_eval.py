from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CodeMesh routing against labeled cases.")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", default="evaluation/reports/routing_latest.json")
    args = parser.parse_args()
    cases = json.loads(Path(__file__).with_name("routing_cases.json").read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]
    rows: list[dict[str, object]] = []
    with httpx.Client(base_url=args.api, timeout=180.0) as client:
        for index, case in enumerate(cases, start=1):
            started = time.perf_counter()
            try:
                response = client.post("/api/v1/route", json={"message": case["prompt"]})
                response.raise_for_status()
                payload = response.json()
                predicted = payload.get("expert")
                error = None
            except Exception as exc:  # preserve a row so failures are measurable
                predicted = None
                payload = {}
                error = str(exc)
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            rows.append(
                {
                    **case,
                    "predicted": predicted,
                    "correct": predicted == case["expected"],
                    "latency_ms": elapsed,
                    "error": error,
                    "fallback": payload.get("routing_fallback", False),
                }
            )
            print(f"{index:03d}/{len(cases)} {case['id']} -> {predicted} ({elapsed:.0f} ms)")
    correct = sum(bool(row["correct"]) for row in rows)
    by_class: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    confusion: Counter[tuple[str, str]] = Counter()
    for row in rows:
        expected = str(row["expected"])
        predicted = str(row["predicted"])
        by_class[expected]["total"] += 1
        by_class[expected]["correct"] += int(bool(row["correct"]))
        confusion[(expected, predicted)] += 1
    report = {
        "cases": len(rows),
        "correct": correct,
        "accuracy": round(correct / len(rows), 4) if rows else 0,
        "average_latency_ms": round(statistics.mean(float(row["latency_ms"]) for row in rows), 2)
        if rows
        else 0,
        "fallback_rate": round(sum(bool(row["fallback"]) for row in rows) / len(rows), 4)
        if rows
        else 0,
        "per_class": {
            key: {**value, "accuracy": round(value["correct"] / value["total"], 4)}
            for key, value in by_class.items()
        },
        "confusion": {
            f"{expected}->{predicted}": count
            for (expected, predicted), count in sorted(confusion.items())
        },
        "rows": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("cases", "correct", "accuracy", "average_latency_ms", "fallback_rate")
            },
            indent=2,
        )
    )
    return 0 if report["accuracy"] >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
