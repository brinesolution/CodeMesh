# CodeMesh

CodeMesh is a local-first, multi-model AI assistant. It routes each request to a focused Ollama specialist while preserving shared session context, structured memory, and a readable chat history.

## Features

- Auto routing plus manual Conversation, Math & Science, and Coding modes
- Runtime-configurable Router / Conversation / STEM / Coding model assignments
- Local Ollama inference with streaming responses and no paid API dependency
- Persistent SQLite sessions, rolling summaries, structured memory, and recovery from raw history
- Context Mesh visualization for graph, context package, timeline, and storage views
- Responsive ChatGPT-like React shell with telemetry, model metadata, KaTeX, and code rendering

## Architecture

```text
User → Router / Context Intelligence → Context Manager → Specialist → Response
                         ↘ SQLite: raw history + memory + summary
```

The router and context-intelligence services choose and assemble the request. The active specialist generates the response through the Ollama gateway. The Context Mesh endpoint exposes a bounded, read-only projection of the selected session; it does not expose hidden reasoning or other sessions.

## Default models

| Role | Default Ollama model |
|---|---|
| Router | `qwen3:0.6b` |
| Conversation | `smollm2:1.7b` |
| Math & Science (STEM) | `qwen3:1.7b` |
| Coding | `qwen2.5-coder:3b` |

Assignments are discovered from the local Ollama catalog and can be changed from the Models section of the existing system/activity panel.

## Requirements

CodeMesh is developed and tested on Windows with Python 3.12 or 3.13, Node.js/npm, `uv`, and Ollama. A minimum of 16 GB RAM is recommended for the configured local models. An NVIDIA GPU with around 8 GB VRAM improves latency, but CPU-only execution is supported with longer response times. Keep several GB of free disk space for Ollama models.

## Quick start (Windows)

```powershell
git clone <repository-url> CodeMesh
Set-Location CodeMesh
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
.\scripts\pull-models.ps1
.\scripts\dev.ps1
```

Open `http://127.0.0.1:5173`. Stop only the services launched by CodeMesh with:

```powershell
.\scripts\stop.ps1
```

The app creates `backend/data/codemesh.db` automatically on first start. Copy `.env.example` to `.env` only when local configuration overrides are needed; the checked-in example contains placeholders and local defaults only.

## Models

The default setup pulls the four models above:

```powershell
ollama pull qwen3:0.6b
ollama pull smollm2:1.7b
ollama pull qwen3:1.7b
ollama pull qwen2.5-coder:3b
```

`.\scripts\pull-models.ps1` verifies Ollama, retries resumable pulls, and checks the configured set.

## Testing

Run the reproducible fast suite from the repository root:

```powershell
.\scripts\test.ps1
```

This runs backend lint/tests and frontend typecheck/build/tests. Live Ollama tests are separate:

```powershell
Set-Location backend
uv run pytest -m live -q
```

See [`docs/TEST_MATRIX.md`](docs/TEST_MATRIX.md) and [`docs/DEMO.md`](docs/DEMO.md) for the verified checks and classroom prompts.

## Context Mesh

Open the mesh button in the sidebar utility area for the selected session. The visualizer presents a bounded semantic graph, the latest assembled context package, a chronological timeline, and read-only SQLite table mappings. It is session-scoped and intended for understanding how context was assembled, not for exposing private model reasoning.

## Project structure

```text
backend/       FastAPI, Ollama gateway, orchestration, SQLite, tests
frontend/      React, TypeScript, Vite chat application
evaluation/    Routing, latency, and context evaluation scripts
scripts/       Windows bootstrap, diagnostics, model setup, launch, and tests
docs/          Architecture, decisions, demos, status, and test evidence
```

## Privacy and local operation

Chat history, context, and model requests stay on the local machine by default. SQLite databases, environments, logs, browser artifacts, and Ollama model files are intentionally excluded from Git. No authentication, billing, cloud deployment, or external model API is included in this local v1.

## Future scope

Docker/AWS seams are documented in [`docs/AWS_FUTURE.md`](docs/AWS_FUTURE.md), but cloud infrastructure is intentionally not implemented in this release.

## Attribution and license

CodeMesh is a student project by Mayank Lohani, Om Jha, and Nihar Bendke. It is released under the MIT License; see [`LICENSE`](LICENSE).
