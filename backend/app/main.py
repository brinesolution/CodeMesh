from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import Settings, get_settings
from app.context.intelligence import ContextIntelligence
from app.context_mesh.service import ContextMeshService
from app.core.orchestrator import Orchestrator
from app.logging_config import configure_logging
from app.models.ollama_client import OllamaClient
from app.models.registry import build_model_registry
from app.persistence.repository import ChatRepository
from app.routing.service import RouterService


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    gateway = OllamaClient(runtime_settings)
    models = build_model_registry(runtime_settings)
    repository = ChatRepository(runtime_settings)
    router_service = RouterService(gateway, models, runtime_settings)
    context_intelligence = ContextIntelligence(gateway, models, runtime_settings)
    orchestrator = Orchestrator(
        settings=runtime_settings,
        gateway=gateway,
        repository=repository,
        models=models,
        router=router_service,
        context_intelligence=context_intelligence,
    )
    context_mesh = ContextMeshService(repository, runtime_settings, models)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(runtime_settings.log_level)
        yield

    app = FastAPI(title="CodeMesh Local API", version="0.1.0", lifespan=lifespan)
    app.state.settings = runtime_settings
    app.state.gateway = gateway
    app.state.models = models
    app.state.repository = repository
    app.state.router_service = router_service
    app.state.context_memory = orchestrator.context_memory
    app.state.context_intelligence = context_intelligence
    app.state.orchestrator = orchestrator
    app.state.context_mesh = context_mesh
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
