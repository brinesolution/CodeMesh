from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    runtime = request.app.state
    runtime_health = await runtime.gateway.health()
    configured = [
        {
            "key": spec.key,
            "model": spec.model,
            "installed": spec.model in {model.name for model in runtime_health.models},
        }
        for spec in runtime.models.values()
    ]
    return {
        "status": "ok",
        "backend": "up",
        "ollama": "up" if runtime_health.reachable else "down",
        "database": "up",
        "models": configured,
    }
