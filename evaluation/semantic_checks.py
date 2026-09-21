"""Small, model-agnostic checks for local evaluation reports."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+(?:,\d{3})*|\d+)(?:\.\d+)?")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("²", "^2").replace("°", " degrees")).strip().lower()


def contains_all(text: str, phrases: Iterable[str]) -> bool:
    value = normalized(text)
    return all(normalized(phrase) in value for phrase in phrases)


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    value = normalized(text)
    return any(normalized(phrase) in value for phrase in phrases)


def contains_number(text: str, expected: float, tolerance: float = 0.01) -> bool:
    for match in NUMBER_PATTERN.finditer(text.replace(",", "")):
        try:
            value = float(match.group(0))
        except ValueError:
            continue
        if math.isclose(value, expected, abs_tol=tolerance, rel_tol=0.0):
            return True
    return False


def has_code_fence(text: str) -> bool:
    return chr(96) * 3 in text


def evaluate_math_answer(
    answer: str,
    *,
    expected_numbers: Iterable[float] = (),
    required_phrases: Iterable[str] = (),
    required_dimensions: Iterable[str] = (),
) -> dict[str, bool]:
    checks = {
        "non_empty": bool(answer.strip()),
        "required_phrases": contains_all(answer, required_phrases),
        "expected_numbers": all(contains_number(answer, value) for value in expected_numbers),
        "required_dimensions": contains_all(answer, required_dimensions),
    }
    checks["passed"] = all(checks.values())
    return checks


def evaluate_code_answer(
    answer: str,
    *,
    required_tokens: Iterable[str] = (),
    require_code_fence: bool = False,
) -> dict[str, bool]:
    checks = {
        "non_empty": bool(answer.strip()),
        "required_tokens": contains_all(answer, required_tokens),
        "code_fence": has_code_fence(answer) if require_code_fence else True,
    }
    checks["passed"] = all(checks.values())
    return checks


def percentile(values: Iterable[float], quantile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, math.ceil(quantile * len(ordered)) - 1))
    return round(ordered[index], 2)
