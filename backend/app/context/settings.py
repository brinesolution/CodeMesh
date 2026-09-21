from __future__ import annotations

import json

from app.context.schemas import (
    ContextIntelligenceSettings,
    ContextSettingsPatch,
    ContextSettingsResponse,
)
from app.persistence.repository import ChatRepository


class ContextSettingsService:
    """Owns durable context-intelligence preferences and effective state."""

    SETTING_KEY = "context_intelligence"

    def __init__(self, repository: ChatRepository) -> None:
        self.repository = repository

    def get(self) -> ContextIntelligenceSettings:
        raw = self.repository.get_application_setting(self.SETTING_KEY)
        if not raw:
            return ContextIntelligenceSettings()
        try:
            return ContextIntelligenceSettings.model_validate(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return ContextIntelligenceSettings()

    def response(self) -> ContextSettingsResponse:
        stored = self.get()
        return ContextSettingsResponse(
            **stored.model_dump(),
            effective=self.effective(stored),
        )

    @staticmethod
    def effective(stored: ContextIntelligenceSettings) -> ContextIntelligenceSettings:
        if stored.shared_context_enabled:
            return stored
        return stored.model_copy(
            update={
                "recent_context_enabled": False,
                "structured_memory_enabled": False,
                "rolling_summary_enabled": False,
                "reference_resolution_enabled": False,
                "smart_context_analysis_enabled": False,
                "historical_changes_enabled": False,
            }
        )

    def update(self, patch: ContextSettingsPatch) -> ContextSettingsResponse:
        current = self.get()
        values = current.model_dump()
        values.update(
            {key: value for key, value in patch.model_dump().items() if value is not None}
        )
        updated = ContextIntelligenceSettings.model_validate(values)
        self.repository.save_application_setting(
            self.SETTING_KEY,
            updated.model_dump_json(),
        )
        return self.response()

    def reset(self) -> ContextSettingsResponse:
        defaults = ContextIntelligenceSettings()
        self.repository.save_application_setting(self.SETTING_KEY, defaults.model_dump_json())
        return self.response()
