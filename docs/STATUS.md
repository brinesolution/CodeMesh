# Status

Current phase: 14/14 repository cleanup and GitHub release preparation complete; local v1 and Context Mesh remain the working deliverable. Docker/AWS deployment is intentionally not started.

Last verified: 2026-09-21. The local stack includes FastAPI/Ollama routing, runtime model assignments, SQLite sessions, Router-driven context intelligence, rolling summaries, bounded structured memory, historical context, raw-history rebuild, streaming, validation, telemetry, fixed responsive chat layout, KaTeX rendering, and Context Mesh.

Verification baseline: 53 fast backend tests passed (5 live tests remain separately selectable), backend Ruff passed, frontend typecheck/build passed, and 16 frontend tests passed. The existing local-v1 evidence remains 6/6 classroom prompts, 20/20 context-stress prompts, persistence/restart recovery, four viewport shell checks, model assignment/reset, and fresh-browser console checks with zero errors.

Context Mesh is session-scoped and bounded. It exposes graph, operational context-package inputs, timeline, and read-only storage mappings; specialist system prompts, hidden reasoning, and other sessions are not returned.

Repository release checks: one root `.env.example`, ignored real SQLite data, environments, logs, browser artifacts, and model files; duplicate/internal release files removed from the working tree; locked `uv`/npm installs; production and development npm audits report zero vulnerabilities; no credential values found in the tracked source/history review.

Fresh-clone gate: a tracked-only detached worktree bootstrapped with `scripts/bootstrap.ps1`, initialized a clean SQLite database, passed failure-state checks, and passed the complete 53-backend/16-frontend test and build suite before being removed.

Performance evidence from local v1 remains documented in `docs/TEST_MATRIX.md`: router-plus-specialist operation, measured route/generation/model-switch latency, RAM/VRAM, and GPU utilization on the target Windows machine.

Next: later Docker/AWS work only. Keep `docs/DEMO.md`, `docs/TEST_MATRIX.md`, and `docs/ARCHITECTURE.md` as the concise recovery and handoff references.
