from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration shared by API and services."""

    model_config = SettingsConfigDict(
        env_prefix="CODEMESH_",
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    ollama_url: str = "http://127.0.0.1:11434"
    router_model: str = "qwen3:0.6b"
    chat_model: str = "smollm2:1.7b"
    stem_model: str = "qwen3:1.7b"
    code_model: str = "qwen2.5-coder:3b"
    context_turns: int = Field(default=6, ge=1, le=12)
    summary_trigger_turns: int = Field(default=8, ge=2, le=100)
    summary_max_chars: int = Field(default=8000, ge=1000, le=20000)
    memory_max_facts: int = Field(default=24, ge=1, le=100)
    memory_max_decisions: int = Field(default=20, ge=1, le=100)
    memory_max_constraints: int = Field(default=20, ge=1, le=100)
    memory_max_preferences: int = Field(default=16, ge=1, le=100)
    memory_max_open_tasks: int = Field(default=16, ge=1, le=100)
    memory_max_topics: int = Field(default=16, ge=1, le=100)
    database_url: str = "sqlite:///./data/codemesh.db"
    demo_mode: bool = False
    log_level: str = "INFO"
    max_prompt_chars: int = Field(default=12000, ge=1000, le=50000)
    max_context_chars: int = Field(default=32000, ge=4000, le=100000)
    ollama_timeout_seconds: float = Field(default=120.0, gt=1, le=900)
    context_analysis_timeout_seconds: float = Field(default=10.0, gt=1, le=60)
    memory_update_timeout_seconds: float = Field(default=12.0, gt=1, le=60)
    summary_update_timeout_seconds: float = Field(default=15.0, gt=1, le=90)
    maintenance_wait_seconds: float = Field(default=1.5, gt=0, le=10)
    route_timeout_seconds: float = Field(default=10.0, gt=1, le=60)
    router_confidence_threshold: float = Field(default=0.60, ge=0, le=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
