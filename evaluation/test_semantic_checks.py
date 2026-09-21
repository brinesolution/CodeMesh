from evaluation.semantic_checks import (
    contains_number,
    evaluate_code_answer,
    evaluate_math_answer,
    percentile,
)


def test_numeric_check_tolerates_latex_and_units() -> None:
    assert contains_number(
        r"$$a = \frac{48\ \mathrm{N}}{24\ \mathrm{kg}} = 2.00\ \mathrm{m/s^2}$$",
        2.0,
    )


def test_math_evaluation_reports_dimension_and_value_checks() -> None:
    result = evaluate_math_answer(
        "Using F = ma, a = 2 m/s^2.",
        expected_numbers=[2],
        required_phrases=["F = ma"],
        required_dimensions=["m/s"],
    )
    assert result["passed"] is True


def test_code_evaluation_is_not_exact_wording_matching() -> None:
    fence = chr(96) * 3
    result = evaluate_code_answer(
        fence
        + "python\ndef calculate_acceleration(force, mass):\n    return force / mass\n"
        + fence,
        required_tokens=["calculate_acceleration", "force", "mass"],
        require_code_fence=True,
    )
    assert result["passed"] is True
    assert percentile([10, 20, 30], 0.9) == 30
