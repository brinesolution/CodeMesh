import json
from collections.abc import AsyncIterator

import httpx

from app.config import Settings
from app.core.errors import GenerationTimeout, ModelNotInstalled, OllamaUnavailable
from app.models.gateway import GenerationResult, ModelGateway, ModelInfo, RuntimeHealth, StreamChunk


class OllamaClient(ModelGateway):
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_url.rstrip("/")
        self.timeout = httpx.Timeout(settings.ollama_timeout_seconds, connect=5.0)

    async def _request_error(self, error: httpx.HTTPStatusError) -> Exception:
        body = error.response.text.lower()
        if error.response.status_code == 404 or "not found" in body or "pull" in body:
            return ModelNotInstalled("The requested Ollama model is not installed.")
        return OllamaUnavailable(f"Ollama returned HTTP {error.response.status_code}.")

    async def health(self) -> RuntimeHealth:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                payload = response.json()
            models = tuple(
                ModelInfo(
                    name=item.get("name", ""),
                    size_bytes=item.get("size"),
                    digest=item.get("digest"),
                )
                for item in payload.get("models", [])
                if item.get("name")
            )
            return RuntimeHealth(True, models)
        except (httpx.HTTPError, OSError) as exc:
            return RuntimeHealth(False, detail=str(exc))

    async def list_models(self) -> list[ModelInfo]:
        result = await self.health()
        if not result.reachable:
            raise OllamaUnavailable(result.detail or "Ollama is not reachable.")
        return list(result.models)

    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ) -> GenerationResult:
        body: dict[str, object] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m" if model.startswith("qwen3:0.6b") else "5m",
            "options": {"temperature": 0.15 if structured else 0.55},
        }
        if structured:
            body["format"] = "json"
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post("/api/chat", json=body)
                response.raise_for_status()
                payload = response.json()
            message = payload.get("message", {})
            return GenerationResult(
                text=str(message.get("content", "")),
                model=model,
                total_duration_ns=payload.get("total_duration"),
                load_duration_ns=payload.get("load_duration"),
                prompt_eval_count=payload.get("prompt_eval_count"),
                eval_count=payload.get("eval_count"),
            )
        except httpx.TimeoutException as exc:
            raise GenerationTimeout("Ollama generation timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise await self._request_error(exc) from exc
        except httpx.RequestError as exc:
            raise OllamaUnavailable("Local Ollama is not reachable.") from exc

    async def stream(
        self, *, model: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[StreamChunk]:
        body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": "5m",
            "options": {"temperature": 0.55},
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                async with client.stream("POST", "/api/chat", json=body) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        payload = json.loads(line)
                        message = payload.get("message", {})
                        yield StreamChunk(
                            text=str(message.get("content", "")),
                            done=bool(payload.get("done", False)),
                            total_duration_ns=payload.get("total_duration"),
                            load_duration_ns=payload.get("load_duration"),
                            eval_count=payload.get("eval_count"),
                        )
        except httpx.TimeoutException as exc:
            raise GenerationTimeout("Ollama streaming timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise await self._request_error(exc) from exc
        except httpx.RequestError as exc:
            raise OllamaUnavailable("Local Ollama is not reachable.") from exc

    async def unload(self, model: str) -> None:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
                response = await client.post(
                    "/api/generate", json={"model": model, "keep_alive": 0}
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise await self._request_error(exc) from exc
        except httpx.RequestError as exc:
            raise OllamaUnavailable("Local Ollama is not reachable.") from exc

