# ruff: noqa: E501
"""Run the Phase 15 live five-chat postfix benchmark in fresh sessions.

This runner uses only the local CodeMesh HTTP API and Ollama-backed responses.
It writes a partial report after every turn so an interrupted run remains
auditable without inventing assistant responses.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from semantic_checks import (
    contains_all,
    evaluate_code_answer,
    evaluate_math_answer,
    percentile,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "reports" / "five_chat_postfix.json"
TERMINAL_MAINTENANCE = {"completed", "failed", "cancelled"}


def now() -> str:
    return datetime.now(UTC).isoformat()


def turn(
    prompt: str,
    route: str,
    *,
    requires_context: bool = False,
    phrases: tuple[str, ...] = (),
    numbers: tuple[float, ...] = (),
    dimensions: tuple[str, ...] = (),
    code_tokens: tuple[str, ...] = (),
    code_fence: bool = False,
) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "expected_route": route,
        "requires_context": requires_context,
        "phrases": phrases,
        "numbers": numbers,
        "dimensions": dimensions,
        "code_tokens": code_tokens,
        "code_fence": code_fence,
    }


SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "POSTFIX-01 Routing Context",
        "objective": "Auto routing, specialist switching, references, and formula continuity.",
        "final_memory_contains": (),
        "turns": [
            turn(
                "Explain in simple terms why clouds appear white during the day.",
                "conversation",
                phrases=("cloud",),
            ),
            turn(
                "A 12 kg object experiences a net force of 48 N. Calculate its acceleration and show the formula.",
                "stem",
                numbers=(4,),
                phrases=("F = ma",),
                dimensions=("m/s",),
            ),
            turn(
                "Write a Python function named calculate_acceleration that takes force and mass and returns the acceleration using the formula from the previous answer.",
                "coding",
                requires_context=True,
                code_tokens=("calculate_acceleration", "force", "mass"),
                code_fence=True,
            ),
            turn(
                "Now explain that Python function to a beginner without changing the code.",
                "conversation|coding",
                requires_context=True,
                phrases=("calculate_acceleration",),
            ),
            turn(
                "If the mass becomes 24 kg but the force remains the same, what is the new acceleration?",
                "stem",
                requires_context=True,
                numbers=(2,),
                dimensions=("m/s",),
            ),
            turn(
                "Modify the earlier Python function so it raises ValueError when mass is zero.",
                "coding",
                requires_context=True,
                code_tokens=("ValueError", "mass"),
                code_fence=True,
            ),
            turn(
                "Give me a two-sentence summary of what we have done so far.",
                "conversation",
                requires_context=True,
                phrases=("acceleration",),
            ),
            turn(
                "Write the Java equivalent of the current acceleration function.",
                "coding",
                requires_context=True,
                code_tokens=("static", "mass"),
                code_fence=True,
            ),
            turn(
                "A car starts from rest with the acceleration we calculated for the 24 kg case. How far does it travel in 10 seconds?",
                "stem",
                requires_context=True,
                numbers=(100,),
                dimensions=("m",),
            ),
            turn(
                "Write Python code that calculates that distance for any acceleration and time.",
                "coding",
                requires_context=True,
                code_tokens=("acceleration", "time"),
                code_fence=True,
            ),
            turn(
                "In plain English, why did the router need different specialists during this conversation?",
                "conversation",
                requires_context=True,
                phrases=("special",),
            ),
            turn(
                "Derive the constant-acceleration displacement equation used earlier when initial velocity is zero.",
                "stem",
                requires_context=True,
                phrases=("acceleration",),
            ),
            turn(
                "Turn that derivation into comments above the Python distance function.",
                "coding",
                requires_context=True,
                code_tokens=("distance", "acceleration"),
                code_fence=True,
            ),
            turn(
                "Which two formulas from this chat are most important? Give only their names and equations.",
                "stem|conversation",
                requires_context=True,
                phrases=("formula",),
            ),
            turn(
                "Summarize the complete progression of this chat from the first question to the latest one in no more than 8 bullet points.",
                "conversation",
                requires_context=True,
                phrases=("cloud",),
            ),
        ],
    },
    {
        "name": "POSTFIX-02 Durable Project Facts",
        "objective": "Canonical facts, replacements, historical values, goals, and bounded memory.",
        "final_memory_contains": ("ORBIT-COPPER-72", "PostgreSQL", "₹96,000", "500"),
        "turns": [
            turn(
                "The project codename is ORBIT-COPPER-72, the project budget is ₹84,000, the backend database is MongoDB, the deadline is 15 October, the target is 500 concurrent users, and the platforms are Android and Web.",
                "conversation",
                phrases=("orbit",),
            ),
            turn(
                "Recap the codename, budget, database, deadline, and target users I just gave you.",
                "conversation",
                requires_context=True,
                phrases=("budget",),
            ),
            turn(
                "Replace MongoDB with PostgreSQL.",
                "conversation",
                requires_context=True,
                phrases=("postgres",),
            ),
            turn(
                "What database is current, and what database did we replace?",
                "conversation",
                requires_context=True,
                phrases=("postgres",),
            ),
            turn(
                "Use Python 3.12 and FastAPI for the service implementation.",
                "coding",
                code_tokens=("python", "fastapi"),
            ),
            turn(
                "The project must work fully offline and must not use external APIs.",
                "conversation",
                requires_context=True,
                phrases=("offline",),
            ),
            turn(
                "The current goal is to add unit tests for this service.",
                "conversation",
                requires_context=True,
                phrases=("unit",),
            ),
            turn(
                "What are the codename, budget, database, and current goal?",
                "conversation",
                requires_context=True,
                phrases=("codename",),
            ),
            turn(
                "Change the project budget to ₹96,000.",
                "conversation",
                requires_context=True,
                phrases=("budget",),
            ),
            turn(
                "What was the old budget and what is the current budget?",
                "conversation",
                requires_context=True,
                phrases=("budget",),
            ),
            turn(
                "How many concurrent users and which deadline did we record?",
                "conversation",
                requires_context=True,
                phrases=("concurrent",),
            ),
            turn(
                "Change the platforms to Windows and Linux.",
                "conversation",
                requires_context=True,
                phrases=("windows",),
            ),
            turn(
                "Which platforms are current?",
                "conversation",
                requires_context=True,
                phrases=("windows",),
            ),
            turn(
                "List the key implementation decisions, including the current database and framework.",
                "conversation",
                requires_context=True,
                phrases=("database",),
            ),
            turn(
                "Summarize the final project facts and the changes we made.",
                "conversation",
                requires_context=True,
                phrases=("orbit",),
            ),
        ],
    },
    {
        "name": "POSTFIX-03 Historical Implementation",
        "objective": "Long-context references, changed implementation choices, and test planning.",
        "final_memory_contains": ("Java 21", "9.80665"),
        "turns": [
            turn(
                "I am building a projectile-motion calculator. Use gravitational acceleration as 9.81 m/s². The user enters initial velocity and launch angle. Calculate maximum height, horizontal range, and flight time.",
                "stem",
                phrases=("gravity",),
            ),
            turn(
                "Use an initial velocity of 30 m/s and launch angle of 40°. Calculate the three outputs.",
                "stem",
                requires_context=True,
                numbers=(30, 40),
                dimensions=("m/s",),
            ),
            turn(
                "Implement the projectile-motion calculator in Python using functions. Validate positive velocity and an angle between 0 and 90 degrees.",
                "coding",
                requires_context=True,
                code_tokens=("python", "function"),
                code_fence=True,
            ),
            turn(
                "Explain the previous implementation and its validation rules.",
                "conversation|coding",
                requires_context=True,
                phrases=("validation",),
            ),
            turn(
                "Do not use Python. Use Java 21 as the final implementation language.",
                "coding",
                requires_context=True,
                phrases=("java",),
            ),
            turn(
                "Rewrite the previous implementation accordingly and retain the calculations.",
                "coding",
                requires_context=True,
                code_tokens=("java",),
                code_fence=True,
            ),
            turn(
                "What implementation language did we settle on?",
                "conversation",
                requires_context=True,
                phrases=("java",),
            ),
            turn(
                "Change the gravity constant to 9.80665 m/s² instead of 9.81.",
                "stem",
                requires_context=True,
                numbers=(9.80665,),
            ),
            turn(
                "What language and gravity values changed historically?",
                "conversation",
                requires_context=True,
                phrases=("gravity",),
            ),
            turn(
                "The goal now is to add unit tests for the calculator.",
                "coding",
                requires_context=True,
                phrases=("test",),
            ),
            turn(
                "List the five test cases we planned.",
                "conversation",
                requires_context=True,
                phrases=("zero",),
            ),
            turn(
                "Using the expected value, verify the horizontal range for 30 m/s at 40° with the current gravity.",
                "stem",
                requires_context=True,
                numbers=(9.80665,),
                dimensions=("m",),
            ),
            turn(
                "Write the JUnit tests we planned using the expected value.",
                "coding",
                requires_context=True,
                code_tokens=("junit", "test"),
                code_fence=True,
            ),
            turn(
                "Summarize the final specification in a concise way.",
                "conversation",
                requires_context=True,
                phrases=("java",),
            ),
            turn(
                "Implement the remaining part from our decisions.",
                "coding",
                requires_context=True,
                code_tokens=("java",),
                code_fence=True,
            ),
        ],
    },
    {
        "name": "POSTFIX-04 Mode Boundary",
        "objective": "Conversation, STEM, coding artifacts, and mode-boundary guardrails in Auto.",
        "final_memory_contains": (),
        "turns": [
            turn(
                "What does a local AI router do? Explain it to a beginner.",
                "conversation",
                phrases=("router",),
            ),
            turn("Calculate 12 times 7 and show the arithmetic.", "stem", numbers=(84,)),
            turn(
                "Generate a JSON configuration for a local assistant with router and specialist roles.",
                "coding",
                code_tokens=("router", "specialist"),
                code_fence=True,
            ),
            turn(
                "Explain that JSON configuration without changing it.",
                "conversation|coding",
                requires_context=True,
                phrases=("json",),
            ),
            turn(
                "Write a Python function that loads the configuration and returns the coding model.",
                "coding",
                requires_context=True,
                code_tokens=("coding", "model"),
                code_fence=True,
            ),
            turn(
                "Why is it useful to separate configuration from orchestration?",
                "conversation",
                requires_context=True,
                phrases=("configuration",),
            ),
            turn(
                "A service has 3 workers and each handles 8 requests per second. What is the total rate?",
                "stem",
                numbers=(24,),
                dimensions=("requests",),
            ),
            turn(
                "Add validation that rejects a missing coding model in the Python function.",
                "coding",
                requires_context=True,
                code_tokens=("coding", "ValueError"),
                code_fence=True,
            ),
            turn(
                "Give a short summary of the architecture we have discussed.",
                "conversation",
                requires_context=True,
                phrases=("router",),
            ),
            turn(
                "Write a SQL query that lists configured model roles.",
                "coding",
                code_tokens=("select", "role"),
                code_fence=True,
            ),
            turn(
                "Explain what the SQL query returns.",
                "conversation|coding",
                requires_context=True,
                phrases=("role",),
            ),
            turn(
                "If each model uses 2 GB and three models are resident, how much memory is that?",
                "stem",
                numbers=(6,),
                dimensions=("GB",),
            ),
            turn(
                "Rewrite the SQL query to order roles alphabetically.",
                "coding",
                requires_context=True,
                code_tokens=("order", "role"),
                code_fence=True,
            ),
            turn(
                "Which specialist handles code artifacts and which handles arithmetic?",
                "conversation",
                requires_context=True,
                phrases=("coding",),
            ),
            turn(
                "Summarize the final routing boundaries in no more than five bullets.",
                "conversation",
                requires_context=True,
                phrases=("conversation",),
            ),
        ],
    },
    {
        "name": "POSTFIX-05 Recovery and Revisions",
        "objective": "Repeated references, replacements, numeric checks, and maintenance recovery.",
        "final_memory_contains": ("LANTERN-RED-9", "PostgreSQL", "100"),
        "turns": [
            turn(
                "The project codename is LANTERN-RED-9 and the launch deadline is 30 November.",
                "conversation",
                phrases=("lantern",),
            ),
            turn(
                "Use SQLite first for the local database and plan for 100 concurrent users.",
                "conversation",
                requires_context=True,
                phrases=("sqlite",),
            ),
            turn(
                "Replace SQLite with PostgreSQL while keeping the same local workflow.",
                "conversation",
                requires_context=True,
                phrases=("postgres",),
            ),
            turn(
                "What database is current and what was the previous one?",
                "conversation",
                requires_context=True,
                phrases=("postgres",),
            ),
            turn(
                "Calculate the throughput if 100 users each make 2 requests per second.",
                "stem",
                requires_context=True,
                numbers=(200,),
                dimensions=("requests",),
            ),
            turn(
                "Write a Python function that estimates that throughput.",
                "coding",
                requires_context=True,
                code_tokens=("throughput", "users"),
                code_fence=True,
            ),
            turn(
                "Explain the function in three short bullets.",
                "conversation|coding",
                requires_context=True,
                phrases=("throughput",),
            ),
            turn(
                "Change the launch deadline to 15 December.",
                "conversation",
                requires_context=True,
                phrases=("december",),
            ),
            turn(
                "What was the old deadline and what is the new deadline?",
                "conversation",
                requires_context=True,
                phrases=("november",),
            ),
            turn(
                "Add an input check that rejects negative request rates.",
                "coding",
                requires_context=True,
                code_tokens=("negative", "ValueError"),
                code_fence=True,
            ),
            turn(
                "Why should that input check be kept?",
                "conversation",
                requires_context=True,
                phrases=("invalid",),
            ),
            turn(
                "If the request rate doubles, what is the new rate from the earlier calculation?",
                "stem",
                requires_context=True,
                numbers=(400,),
            ),
            turn(
                "Write a JSON example containing the codename, current database, and new deadline.",
                "coding",
                requires_context=True,
                code_tokens=("codename", "database", "deadline"),
                code_fence=True,
            ),
            turn(
                "Which project facts were revised during this chat?",
                "conversation",
                requires_context=True,
                phrases=("database",),
            ),
            turn(
                "Summarize the current project state and the historical replacements.",
                "conversation",
                requires_context=True,
                phrases=("postgres",),
            ),
        ],
    },
]


def get_json(client: httpx.Client, path: str) -> dict[str, Any]:
    response = client.get(path)
    response.raise_for_status()
    return response.json()


def save_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def check_turn(spec: dict[str, Any], answer: str) -> dict[str, Any]:
    if spec["code_tokens"]:
        return evaluate_code_answer(
            answer,
            required_tokens=spec["code_tokens"],
            require_code_fence=spec["code_fence"],
        )
    if spec["numbers"] or spec["dimensions"]:
        return evaluate_math_answer(
            answer,
            expected_numbers=spec["numbers"],
            required_phrases=spec["phrases"],
            required_dimensions=spec["dimensions"],
        )
    return {
        "non_empty": bool(answer.strip()),
        "required_phrases": contains_all(answer, spec["phrases"]),
        "passed": bool(answer.strip()) and contains_all(answer, spec["phrases"]),
    }


def route_matches(expected: str, actual: str | None) -> bool:
    return actual is not None and actual in expected.split("|")


def stream_turn(
    client: httpx.Client,
    session_id: str,
    prompt: str,
    *,
    timeout: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    answer_parts: list[str] = []
    route: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    stream_completed = False
    try:
        with client.stream(
            "POST",
            "/api/v1/chat/stream",
            json={"message": prompt, "mode": "auto", "session_id": session_id},
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                event_type = event.get("type")
                data = event.get("data") or {}
                if event_type == "route":
                    route = data
                elif event_type == "token":
                    answer_parts.append(str(data.get("text", "")))
                elif event_type == "metrics":
                    metrics = data
                elif event_type == "error":
                    errors.append(data)
                elif event_type == "done":
                    stream_completed = True
                    if not route:
                        route = data.get("route") or {}
                    if not metrics:
                        metrics = data.get("metrics") or {}
    except Exception as exc:
        errors.append({"code": type(exc).__name__, "message": str(exc)})
    return {
        "timestamp_sent": now(),
        "timestamp_completed": now(),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "assistant_output": "".join(answer_parts).strip(),
        "route": route,
        "metrics": metrics,
        "stream_completed": stream_completed,
        "raw_errors": errors,
    }


def flatten_memory(mesh: dict[str, Any]) -> str:
    memory = mesh.get("memory") or {}
    items = [
        item.get("text", "")
        for category in ("facts", "decisions", "constraints", "preferences", "open_tasks")
        for item in memory.get(category, [])
    ]
    if memory.get("current_goal"):
        items.append(str(memory["current_goal"]))
    return " ".join(items).lower()


def finalize_chat(
    client: httpx.Client,
    session_id: str,
    scenario: dict[str, Any],
    turns: list[dict[str, Any]],
    maintenance_wait: float,
) -> dict[str, Any]:
    deadline = time.perf_counter() + maintenance_wait
    mesh: dict[str, Any] = {}
    while True:
        mesh = get_json(client, f"/api/v1/sessions/{session_id}/mesh")
        maintenance = mesh.get("latest_maintenance") or {}
        if maintenance.get("status") in TERMINAL_MAINTENANCE:
            break
        if time.perf_counter() >= deadline:
            break
        time.sleep(0.75)
    session = get_json(client, f"/api/v1/sessions/{session_id}")
    memory_text = flatten_memory(mesh)
    final_checks = {
        "raw_messages": len(session.get("messages", [])) == len(turns) * 2,
        "assistant_turns": len(
            [item for item in session.get("messages", []) if item["role"] == "assistant"]
        )
        == len(turns),
        "memory_expectations": all(
            value.lower() in memory_text for value in scenario["final_memory_contains"]
        ),
        "maintenance_terminal": (mesh.get("latest_maintenance") or {}).get("status")
        in TERMINAL_MAINTENANCE,
    }
    return {
        "session": {
            "id": session_id,
            "title": session.get("title"),
            "message_count": len(session.get("messages", [])),
        },
        "context_observation": {
            "memory_item_count": sum(
                len((mesh.get("memory") or {}).get(category, []))
                for category in ("facts", "decisions", "constraints", "preferences", "open_tasks")
            ),
            "summary_length": len((mesh.get("summary") or {}).get("text", "")),
            "recent_context_count": (mesh.get("recent_context") or {}).get("count", 0),
            "latest_maintenance": mesh.get("latest_maintenance"),
            "context_settings": mesh.get("context_settings"),
        },
        "final_checks": final_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--maintenance-wait", type=float, default=45.0)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "test_suite": "CodeMesh Phase 15 Five-Chat Postfix Benchmark",
        "test_type": "live_new_sessions",
        "started_at": now(),
        "api": args.api,
        "scenarios": len(SCENARIOS),
        "chats": [],
        "errors": [],
    }
    with httpx.Client(base_url=args.api, timeout=args.timeout) as client:
        for index, scenario in enumerate(SCENARIOS, start=1):
            created = client.post(
                "/api/v1/sessions",
                json={"preferred_mode": "auto", "title": scenario["name"]},
            )
            created.raise_for_status()
            session_id = created.json()["id"]
            chat_report: dict[str, Any] = {
                "name": scenario["name"],
                "objective": scenario["objective"],
                "session_id": session_id,
                "turns": [],
            }
            report["chats"].append(chat_report)
            save_report(args.output, report)
            for turn_number, spec in enumerate(scenario["turns"], start=1):
                result = stream_turn(
                    client,
                    session_id,
                    spec["prompt"],
                    timeout=args.timeout,
                )
                actual_route = (result["route"] or {}).get("expert")
                assessment = check_turn(spec, result["assistant_output"])
                row = {
                    "turn": turn_number,
                    "user_input": spec["prompt"],
                    "expected_route": spec["expected_route"],
                    "actual_route": actual_route,
                    "route_correct": route_matches(spec["expected_route"], actual_route),
                    "requires_context": spec["requires_context"],
                    "context_observation": {
                        "recent_message_count": (result["metrics"].get("context") or {}).get(
                            "recent_message_count", 0
                        ),
                        "reference_detected": (result["metrics"].get("context") or {})
                        .get("context_analysis", {})
                        .get("reference_detected", False),
                        "memory_update_status": (result["metrics"].get("context") or {}).get(
                            "memory_update_status"
                        ),
                    },
                    "assistant_output": result["assistant_output"],
                    "stream_completed": result["stream_completed"],
                    "elapsed_ms": result["elapsed_ms"],
                    "metrics": result["metrics"],
                    "assessment": assessment,
                    "raw_errors": result["raw_errors"],
                }
                chat_report["turns"].append(row)
                if result["raw_errors"]:
                    report["errors"].extend(
                        [
                            {"chat": scenario["name"], "turn": turn_number, **error}
                            for error in result["raw_errors"]
                        ]
                    )
                save_report(args.output, report)
                print(
                    f"{index}/5 {scenario['name']} turn {turn_number:02d}/15 "
                    f"route={actual_route or 'missing'} elapsed={result['elapsed_ms']:.0f}ms "
                    f"complete={result['stream_completed']}"
                )
            chat_report["final"] = finalize_chat(
                client,
                session_id,
                scenario,
                chat_report["turns"],
                args.maintenance_wait,
            )
            save_report(args.output, report)
            print(f"{scenario['name']} final checks: {chat_report['final']['final_checks']}")

    all_turns = [turn for chat in report["chats"] for turn in chat["turns"]]
    route_correct = sum(bool(turn["route_correct"]) for turn in all_turns)
    complete = sum(bool(turn["stream_completed"]) for turn in all_turns)
    context_turns = [turn for turn in all_turns if turn["requires_context"]]
    context_success = sum(
        bool(
            (turn["context_observation"]["recent_message_count"] or 0) > 0
            or turn["context_observation"]["reference_detected"]
        )
        for turn in context_turns
    )
    latencies = [float(turn["elapsed_ms"]) for turn in all_turns]
    report["summary"] = {
        "chat_count": len(report["chats"]),
        "turn_count": len(all_turns),
        "complete_turns": complete,
        "missing_turns": len(all_turns) - complete,
        "route_correct": route_correct,
        "route_accuracy": round(route_correct / len(all_turns), 4) if all_turns else 0,
        "context_reference_turns": len(context_turns),
        "context_reference_success": context_success,
        "context_reference_accuracy": round(context_success / len(context_turns), 4)
        if context_turns
        else 1,
        "response_check_passes": sum(bool(turn["assessment"].get("passed")) for turn in all_turns),
        "response_check_accuracy": round(
            sum(bool(turn["assessment"].get("passed")) for turn in all_turns) / len(all_turns), 4
        )
        if all_turns
        else 0,
        "latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p90": percentile(latencies, 0.90),
            "max": round(max(latencies), 2) if latencies else 0,
            "mean": round(statistics.mean(latencies), 2) if latencies else 0,
        },
        "errors": len(report["errors"]),
        "final_checks_passed": sum(
            all(bool(value) for value in chat.get("final", {}).get("final_checks", {}).values())
            for chat in report["chats"]
        ),
    }
    report["completed_at"] = now()
    save_report(args.output, report)
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["missing_turns"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
