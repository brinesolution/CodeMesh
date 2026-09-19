import ast
import re

from app.validation.base import ValidationResult

PYTHON_BLOCK = re.compile(r"```python\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def validate_python_response(text: str) -> ValidationResult:
    blocks = PYTHON_BLOCK.findall(text)
    if not blocks:
        return ValidationResult("python_syntax", "not_applicable", "No fenced Python block found.")
    try:
        for block in blocks:
            ast.parse(block)
    except SyntaxError as exc:
        return ValidationResult("python_syntax", "invalid", f"Syntax error on line {exc.lineno}.")
    return ValidationResult("python_syntax", "valid", "Python syntax is valid.")

