from app.config import Settings
from app.core.orchestrator import Orchestrator
from app.models.gateway import GenerationResult, RuntimeHealth, StreamChunk
from app.models.registry import build_model_registry
from app.persistence.repository import ChatRepository
from app.routing.service import RouterService


class RebuildGateway:
    async def generate(
        self, *, model: str, messages: list[dict[str, str]], structured: bool = False
    ):
        system = messages[0]["content"]
        if "context analyst" in system:
            payload = (
                '{"topic":"recovered project","requires_history":true,'
                '"recent_turns_needed":1}'
            )
        elif "memory extractor" in system:
            payload = (
                '{"changes":[{"category":"facts",'
                '"text":"Recovered from raw history."}],"memory_worthy":true}'
            )
        else:
            payload = '{"summary":"Recovered project context from the persisted conversation."}'
        return GenerationResult(payload, model)

    async def stream(self, *, model: str, messages: list[dict[str, str]]):
        yield StreamChunk(done=True)

    async def health(self):
        return RuntimeHealth(True)

    async def list_models(self):
        return []

    async def unload(self, model: str):
        return None


async def test_rebuild_context_rederives_state_without_changing_raw_history(tmp_path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'rebuild.db'}",
        context_turns=1,
        summary_trigger_turns=2,
    )
    gateway = RebuildGateway()
    repository = ChatRepository(settings)
    session_id = repository.create_session().id
    repository.add_message(session_id, role="user", content="We chose Python.")
    repository.add_message(session_id, role="assistant", content="Python is selected.")
    repository.add_message(session_id, role="user", content="Now add tests.")
    repository.add_message(session_id, role="assistant", content="Tests were added.")
    raw_before = [(item.role, item.content) for item in repository.all_messages(session_id)]
    models = build_model_registry(settings)
    router = RouterService(gateway, models, settings)
    orchestrator = Orchestrator(
        settings=settings,
        gateway=gateway,
        repository=repository,
        models=models,
        router=router,
    )

    rebuilt = await orchestrator.rebuild_context(session_id)

    assert rebuilt["current_topic"] == "recovered project"
    assert rebuilt["memory"]["facts"][0]["text"] == "Recovered from raw history."
    assert rebuilt["summary"] == "Recovered project context from the persisted conversation."
    assert [(item.role, item.content) for item in repository.all_messages(session_id)] == raw_before
