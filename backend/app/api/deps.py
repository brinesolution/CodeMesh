from fastapi import Request

from app.config import Settings


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings

