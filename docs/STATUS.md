# Status

Current phase: Phases 1–10, Context Mesh/release hardening, and the Phase 15 controlled stress-testing pass are complete. Local v1 remains the working deliverable; Docker/AWS deployment is intentionally not started.

Last verified: 2026-09-22. The local stack includes FastAPI/Ollama routing, runtime model assignments, SQLite sessions, Router-driven context intelligence, rolling summaries, bounded structured memory, historical context, raw-history rebuild, streaming, validation, telemetry, fixed responsive chat layout, KaTeX rendering, and Context Mesh.

Final verification: 77 fast backend tests passed (5 live tests passed separately), evaluation semantic checks passed 3/3, backend Ruff passed, frontend typecheck/build passed, and 19 frontend tests passed. Formal routing scored 120/120 (100.00%); the five-chat postfix pass completed 75/75 turns with 75/75 routes, 63/63 context-reference checks, zero errors, and all five final checks. The six classroom prompts passed 6/6 with exact specialist models. Browser checks covered 1920×1080, 1366×768, 1024×768, and 390×844 with fixed-shell scroll independence, Auto new-chat default, streaming Stop visibility, model configuration, mobile drawer, and zero console errors.

The protected baseline evaluation/reports/five_chat_stress_test.json remains unchanged at SHA256 97FD3AFCEBCB1FE0A4138B4F654EBCF7ECE8BB5FACCE40BD3B07227C8FC396BD.

Context Mesh is session-scoped and bounded. It exposes graph, operational context-package inputs, timeline, and read-only storage mappings; specialist system prompts, hidden reasoning, and other sessions are not returned.

Repository release checks: one root `.env.example`, ignored real SQLite data, environments, logs, browser artifacts, and model files; duplicate/internal release files removed from the working tree; locked `uv`/npm installs; production and development npm audits report zero vulnerabilities; no credential values found in the tracked source/history review; Windows `dev.ps1` launch and `stop.ps1` cleanup verified.

Fresh-clone gate: a tracked-only detached worktree bootstrapped with `scripts/bootstrap.ps1`, initialized a clean SQLite database, passed failure-state checks, and passed the complete 53-backend/16-frontend test and build suite before being removed.

Performance evidence from local v1 remains documented in `docs/TEST_MATRIX.md`: router-plus-specialist operation, measured route/generation/model-switch latency, RAM/VRAM, and GPU utilization on the target Windows machine.

Next: later Docker/AWS work only. Keep `docs/DEMO.md`, `docs/TEST_MATRIX.md`, and `docs/ARCHITECTURE.md` as the concise recovery and handoff references.
