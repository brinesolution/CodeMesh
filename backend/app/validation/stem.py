import re

from app.validation.base import ValidationResult


def validate_stem_response(prompt: str, response: str) -> ValidationResult:
    match = re.search(r"(\d+(?:\.\d+)?)\s*\s*kg.*?(\d+(?:\.\d+)?)\s*\s*N", prompt, re.I | re.S)
    if not match:
        return ValidationResult(
            "stem_check", "not_applicable", "No unambiguous simple equation found."
        )
    mass, force = map(float, match.groups())
    expected = force / mass if mass else None
    if expected is None:
        return ValidationResult("stem_check", "not_applicable")
    answer_matches = re.findall(
        r"(?:=|is|equals)\s*(\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)?", response, re.I
    )
    if answer_matches and abs(float(answer_matches[-1]) - expected) < 1e-6:
        return ValidationResult("stem_check", "valid", "Simple force/mass result matches.")
    return ValidationResult(
        "stem_check", "not_applicable", "Response format was not deterministic enough."
    )
