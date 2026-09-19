| Area | Command/check | Status |
|---|---|---|
| Backend unit/integration/failure | `uv run pytest -q` | passing: 36 passed, 5 live deselected |
| Backend lint | `uv run ruff check app tests` | passing |
| Frontend typecheck/build | `npm run typecheck; npm run build` | passing |
| Frontend tests | `npm test` | passing: 12 tests |
| Model configuration | `/api/v1/models`; Models tab; assignment and reset flow | passing: 14 live Ollama models discovered; all four role selectors updated; defaults restored |
| Live models | `scripts/verify-models.ps1`; `uv run pytest -m live -q` | passing: 4 installed, 5 live tests |
| Classroom prompts | `docs/DEMO.md` prompts through `/api/v1/chat` | passing: 6/6, exact specialist models |
| Routing | `uv run --directory backend python ../evaluation/run_routing_eval.py` | passing: 118/120, 98.33% |
| Performance | `evaluation/run_latency_eval.py --rounds 7` | passing: 21 specialist requests; route, switch, generation, RAM/VRAM/GPU recorded |
| Browser | `scripts/browser-smoke.ps1`; Playwright fixed-shell checks at 1920x1080, 1366x768, 1024x768, and 390x844 | passing; independent sidebar/message scroll, fixed footer/header/composer, mobile drawer, live stream, telemetry, Models panel, Auto new chat, and console errors 0 verified |
| Context and memory | `uv run pytest -q tests/unit/test_context_*.py tests/integration/test_context_*.py` | passing: Router analysis normalization/fallback, memory dedupe/conflict/caps, summary batching, session isolation, specialist package, maintenance failure, and raw-history rebuild |
| Long conversation and recovery | 40-turn bounded unit test; 30-turn live session; backend restart; rebuild endpoint | passing: raw messages preserved, summary boundary persisted, context survived restart, rebuild rederived context |
| Router model switch | live `PUT /api/v1/models/router`, Auto chat, restore defaults | passing: route and context tasks both used the assigned `qwen3:1.7b`; defaults restored to `qwen3:0.6b` |
