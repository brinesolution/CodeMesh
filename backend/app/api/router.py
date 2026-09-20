from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.context_mesh import router as context_mesh_router
from app.api.routes.health import router as health_router
from app.api.routes.models import router as models_router
from app.api.routes.routing import router as routing_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.system import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(context_mesh_router)
api_router.include_router(models_router)
api_router.include_router(routing_router)
api_router.include_router(sessions_router)
api_router.include_router(system_router)
