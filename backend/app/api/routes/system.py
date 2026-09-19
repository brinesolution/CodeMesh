from fastapi import APIRouter, Request

from app.telemetry.system import system_snapshot

router = APIRouter(tags=["system"])


@router.get("/system")
async def system(request: Request) -> dict[str, object | None]:
    health = await request.app.state.gateway.health()
    active = request.app.state.orchestrator.lifecycle.active_specialist
    return system_snapshot(active_model=active, ollama_reachable=health.reachable)

