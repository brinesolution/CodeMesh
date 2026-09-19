import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    mode: str = Field(default="auto", pattern="^(auto|conversation|stem|coding)$")
    session_id: str | None = None


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request) -> dict[str, object]:
    return await request.app.state.orchestrator.chat(
        message=payload.message, mode=payload.mode, session_id=payload.session_id
    )


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        async for event in request.app.state.orchestrator.stream_chat(
            message=payload.message, mode=payload.mode, session_id=payload.session_id
        ):
            yield json.dumps(event, separators=(",", ":")) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")

