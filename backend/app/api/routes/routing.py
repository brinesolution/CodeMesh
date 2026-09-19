from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["routing"])


class RouteRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)


@router.post("/route")
async def route(payload: RouteRequest, request: Request) -> dict[str, object]:
    result = await request.app.state.router_service.route(payload.message)
    return result.model_dump(mode="json")

