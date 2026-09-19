from app.experts.base import ExpertDefinition
from app.experts.coding import CODING_EXPERT
from app.experts.conversation import CONVERSATION_EXPERT
from app.experts.stem import STEM_EXPERT

EXPERTS: dict[str, ExpertDefinition] = {
    expert.key: expert for expert in (CONVERSATION_EXPERT, STEM_EXPERT, CODING_EXPERT)
}


def get_expert(key: str) -> ExpertDefinition:
    try:
        return EXPERTS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown expert: {key}") from exc

