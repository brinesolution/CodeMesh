from app.validation.code import validate_python_response
from app.validation.stem import validate_stem_response


def test_python_validator_reports_valid_syntax_without_execution() -> None:
    result = validate_python_response("```python\ndef add(a, b):\n    return a + b\n```")

    assert result.status == "valid"
    assert result.kind == "python_syntax"


def test_python_validator_rejects_invalid_syntax() -> None:
    result = validate_python_response("```python\ndef broken(:\n    pass\n```")

    assert result.status == "invalid"


def test_stem_validator_checks_simple_force_mass_result() -> None:
    result = validate_stem_response(
        "A 5 kg body experiences a force of 20 N.", "a = 20 / 5 = 4 m/s^2"
    )

    assert result.status == "valid"
