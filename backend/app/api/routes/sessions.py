from fastapi import APIRouter, HTTPException, Request

from app.persistence.schemas import SessionCreate, SessionDetail, SessionSummary

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(request: Request):
    return request.app.state.repository.list_sessions()


@router.post("/sessions", response_model=SessionSummary)
def create_session(payload: SessionCreate, request: Request):
    return request.app.state.repository.create_session(payload.preferred_mode)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, request: Request):
    session = request.app.state.repository.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, request: Request):
    if not request.app.state.repository.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}

