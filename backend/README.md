# Backend

Purpose: FastAPI orchestration, Ollama gateway, persistence, validation, and telemetry.

Entry point: `app/main.py` via `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`.

Tests: `uv run pytest`; lint: `uv run ruff check app tests`.

Status: local API implemented; live model verification depends on Ollama.

