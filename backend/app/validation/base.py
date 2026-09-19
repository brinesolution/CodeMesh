from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    kind: str
    status: str
    detail: str | None = None

