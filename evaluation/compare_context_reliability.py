"""Compare the preserved baseline stress report with the Phase 15 postfix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "reports" / "five_chat_stress_test.json"
POSTFIX = ROOT / "reports" / "five_chat_postfix.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route_matches(expected: str, actual: str | None) -> bool:
    return actual is not None and actual in expected.split("|")


def baseline_metrics(report: dict[str, Any]) -> dict[str, Any]:
    turns = [turn for chat in report.get("chats", []) for turn in chat.get("turns", [])]
    complete = [
        turn
        for turn in turns
        if turn.get("streaming", {}).get("completed_normally")
        and turn.get("actual", {}).get("assistant_output", "").strip()
    ]
    route_correct = sum(
        route_matches(
            str(turn.get("expected", {}).get("route", "")),
            turn.get("actual", {}).get("route"),
        )
        for turn in turns
    )
    context_expected = [
        turn for turn in turns if turn.get("expected", {}).get("context_requirements")
    ]
    context_success = sum(
        turn.get("context_observation", {}).get("referenced_required_prior_information") is True
        for turn in context_expected
    )
    return {
        "chat_count": len(report.get("chats", [])),
        "turn_count": len(turns),
        "complete_turns": len(complete),
        "missing_turns": len(turns) - len(complete),
        "route_correct": route_correct,
        "route_accuracy": round(route_correct / len(turns), 4) if turns else 0,
        "context_reference_turns": len(context_expected),
        "context_reference_success": context_success,
        "context_reference_accuracy": round(context_success / len(context_expected), 4)
        if context_expected
        else 1,
        "errors": sum(1 for turn in turns if turn.get("assessment", {}).get("status") == "ERROR"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--postfix", type=Path, default=POSTFIX)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reports" / "context_reliability_comparison.json"
    )
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    postfix = json.loads(args.postfix.read_text(encoding="utf-8"))
    baseline_summary = baseline_metrics(baseline)
    postfix_summary = postfix.get("summary", {})
    comparison = {
        "baseline": {
            "path": str(args.baseline),
            "sha256": sha256(args.baseline),
            "metrics": baseline_summary,
        },
        "postfix": {
            "path": str(args.postfix),
            "sha256": sha256(args.postfix),
            "metrics": postfix_summary,
        },
        "delta": {
            "route_accuracy": round(
                float(postfix_summary.get("route_accuracy", 0))
                - float(baseline_summary.get("route_accuracy", 0)),
                4,
            ),
            "complete_turns": int(postfix_summary.get("complete_turns", 0))
            - int(baseline_summary.get("complete_turns", 0)),
            "missing_turns": int(postfix_summary.get("missing_turns", 0))
            - int(baseline_summary.get("missing_turns", 0)),
            "context_reference_accuracy": round(
                float(postfix_summary.get("context_reference_accuracy", 0))
                - float(baseline_summary.get("context_reference_accuracy", 0)),
                4,
            ),
            "errors": int(postfix_summary.get("errors", 0))
            - int(baseline_summary.get("errors", 0)),
        },
        "baseline_preserved_for_comparison": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    print(json.dumps(comparison, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
