"""Validate a completed real-UI context stress session.

The prompts are intentionally sent through the browser during acceptance testing.
This script checks the persisted session afterward; it is not a substitute for UI execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "context_stress_cases.json"


def get_json(url: str) -> object:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - local URL is explicit CLI input
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        raise SystemExit(f"Could not read {url}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if len(cases) != 20:
        raise SystemExit(f"Expected 20 stress cases, found {len(cases)}")

    session_url = f"{args.base_url.rstrip('/')}/api/v1/sessions/{args.session_id}"
    session = get_json(session_url)
    context = get_json(f"{session_url}/context")
    messages = session["messages"]
    user_messages = [message for message in messages if message["role"] == "user"]
    assistant_messages = [message for message in messages if message["role"] == "assistant"]

    prompt_match = len(user_messages) == len(cases) and all(
        actual["content"] == case["prompt"] for actual, case in zip(user_messages, cases)
    )
    memory = context["memory"]
    memory_items = [
        item
        for category in ("facts", "decisions", "constraints", "preferences", "open_tasks")
        for item in memory.get(category, [])
    ]
    memory_ids = [item["id"] for item in memory_items]
    history_answer = assistant_messages[18]["content"] if len(assistant_messages) >= 19 else ""
    final_answer = assistant_messages[19]["content"] if len(assistant_messages) >= 20 else ""
    summary = context.get("summary", "")

    checks = {
        "twenty_exact_user_prompts": len(user_messages) == 20 and prompt_match,
        "forty_raw_messages": len(messages) == 40,
        "durable_goal": memory.get("current_goal") == "Add unit tests for the projectile-motion calculator.",
        "updated_gravity": any(
            item["id"] == "projectile-gravity" and "9.80665" in item["text"]
            for item in memory.get("facts", [])
        ),
        "java_decision": any(
            item["id"] == "implementation-language" and "Java 21" in item["text"]
            for item in memory.get("decisions", [])
        ),
        "five_open_test_tasks": len(memory.get("open_tasks", [])) == 5,
        "bounded_recent_context": context.get("recent_context_turns", 0) <= 12,
        "bounded_summary": len(summary) <= 12000,
        "historical_summary": "Language history: Python -> Java 21." in summary
        and "Gravity history: 9.81 -> 9.80665" in summary,
        "unique_memory_ids": len(memory_ids) == len(set(memory_ids)),
        "historical_answer": all(
            token in history_answer for token in ("Python", "Java", "9.81", "9.80665")
        ),
        "final_implementation": "junit" in final_answer.lower() and "```" in final_answer,
    }
    route_counts: dict[str, int] = {}
    for message in assistant_messages:
        route = message.get("route") or "unknown"
        route_counts[route] = route_counts.get(route, 0) + 1

    report = {
        "session_id": args.session_id,
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "message_count": len(messages),
        "user_turns": len(user_messages),
        "assistant_turns": len(assistant_messages),
        "summary_length": len(summary),
        "summary_through_message_id": context.get("summary_through_message_id"),
        "memory_item_count": len(memory_items),
        "route_counts": route_counts,
        "final_goal": memory.get("current_goal"),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
