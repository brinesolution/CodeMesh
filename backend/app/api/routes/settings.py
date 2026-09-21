from fastapi import APIRouter, Request

from app.context.schemas import ContextSettingsPatch, ContextSettingsResponse

router = APIRouter(tags=["settings"])


@router.get("/settings/context", response_model=ContextSettingsResponse)
def get_context_settings(request: Request) -> ContextSettingsResponse:
    return request.app.state.context_settings.response()


@router.patch("/settings/context", response_model=ContextSettingsResponse)
def update_context_settings(
    payload: ContextSettingsPatch, request: Request
) -> ContextSettingsResponse:
    return request.app.state.context_settings.update(payload)


@router.post("/settings/context/reset", response_model=ContextSettingsResponse)
def reset_context_settings(request: Request) -> ContextSettingsResponse:
    return request.app.state.context_settings.reset()
