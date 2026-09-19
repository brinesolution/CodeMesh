from fastapi import APIRouter, Request

router = APIRouter(tags=["models"])


@router.get("/models")
async def models(request: Request) -> dict[str, object]:
    runtime = request.app.state
    health = await runtime.gateway.health()
    installed = {model.name for model in health.models}
    configured = [
        {
            "key": spec.key,
            "model": spec.model,
            "label": spec.label,
            "role": spec.role,
            "installed": spec.model in installed,
        }
        for spec in runtime.models.values()
    ]
    return {
        "ollama_reachable": health.reachable,
        "models": configured,
        "active_model": runtime.orchestrator.lifecycle.active_specialist,
    }

