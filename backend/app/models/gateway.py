from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelInfo:
    name: str
    size_bytes: int | None = None
    digest: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    total_duration_ns: int | None = None
    load_duration_ns: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None


@dataclass(frozen=True)
class StreamChunk:
    text: str = ""
    done: bool = False
    total_duration_ns: int | None = None
    load_duration_ns: int | None = None
    eval_count: int | None = None


@dataclass(frozen=True)
class RuntimeHealth:
    reachable: bool
    models: tuple[ModelInfo, ...] = ()
    detail: str | None = None


class ModelGateway(Protocol):
    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ) -> GenerationResult: ...

    def stream(
        self, *, model: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[StreamChunk]: ...

    async def list_models(self) -> list[ModelInfo]: ...

    async def health(self) -> RuntimeHealth: ...

    async def unload(self, model: str) -> None: ...

