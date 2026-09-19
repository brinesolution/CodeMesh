from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.models.gateway import RuntimeHealth

MODEL_ROLES = ("router", "conversation", "stem", "coding")


class ModelAssignment(BaseModel):
    model: str = Field(min_length=1, max_length=100)

router = APIRouter(tags=["models"])


def _configuration(request: Request, health: RuntimeHealth) -> dict[str, object]:
    runtime = request.app.state
    installed = [
        {
            "name": model.name,
            "size_bytes": model.size_bytes,
            "digest": model.digest,
        }
        for model in health.models
    ]
    installed_names = {model["name"] for model in installed}
    configured = [
        {
            "key": spec.key,
            "model": spec.model,
            "label": spec.label,
            "role": spec.role,
            "installed": spec.model in installed_names,
        }
        for spec in runtime.models.values()
    ]
    return {
        "ollama_reachable": health.reachable,
        "available_models": installed,
        "models": configured,
        "assignments": runtime.models.assignments(),
        "defaults": runtime.models.defaults(),
        "active_model": runtime.orchestrator.lifecycle.active_specialist,
    }


@router.get("/models")
async def models(request: Request) -> dict[str, object]:
    health = await request.app.state.gateway.health()
    return _configuration(request, health)


@router.post("/models/reset")
async def reset_models(request: Request) -> dict[str, object]:
    runtime = request.app.state
    runtime.models.restore_defaults()
    return _configuration(request, await runtime.gateway.health())


@router.put("/models/{role}")
async def assign_model(role: str, payload: ModelAssignment, request: Request) -> dict[str, object]:
    if role not in MODEL_ROLES:
        raise HTTPException(status_code=404, detail=f"Unknown model role: {role}")

    runtime = request.app.state
    health = await runtime.gateway.health()
    if not health.reachable:
        raise HTTPException(status_code=503, detail="Ollama is not reachable.")
    installed_names = {model.name for model in health.models}
    if payload.model not in installed_names:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{payload.model}' is not installed in Ollama.",
        )

    runtime.models.assign_model(role, payload.model)
    return _configuration(request, health)
