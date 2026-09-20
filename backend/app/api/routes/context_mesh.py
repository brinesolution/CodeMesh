from fastapi import APIRouter, HTTPException, Request

from app.context_mesh.schemas import ContextMeshResponse

router = APIRouter(tags=["context-mesh"])


@router.get("/sessions/{session_id}/mesh", response_model=ContextMeshResponse)
def get_context_mesh(session_id: str, request: Request) -> ContextMeshResponse:
    mesh = request.app.state.context_mesh.get(session_id)
    if mesh is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return mesh
