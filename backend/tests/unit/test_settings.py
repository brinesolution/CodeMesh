from app.config import Settings


def test_settings_keep_directive_model_stack_and_local_defaults() -> None:
    settings = Settings()

    assert settings.ollama_url == "http://127.0.0.1:11434"
    assert settings.router_model == "qwen3:0.6b"
    assert settings.chat_model == "smollm2:1.7b"
    assert settings.stem_model == "qwen3:1.7b"
    assert settings.code_model == "qwen2.5-coder:3b"
