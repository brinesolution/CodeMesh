| Area | Command/check | Status |
|---|---|---|
| Backend unit/integration/failure | `.\scripts\test.ps1` | passing: 47 passed, 5 live deselected |
| Backend lint | `uv run ruff check app tests` | passing |
| Frontend typecheck/build | `npm run typecheck; npm run build` | passing |
| Frontend tests | `npm test` | passing: 12 tests |
| Model configuration | `/api/v1/models`; Models tab; assignment and reset flow | passing: 14 live Ollama models discovered; all four role selectors updated; defaults restored to exact assignments |
| Live models | `scripts/verify-models.ps1`; `uv run pytest -m live -q` | passing: 4 installed, 5 live tests |
| Classroom prompts | `docs/DEMO.md` prompts through `/api/v1/chat` | passing: 6/6, exact specialist models |
| Routing | `uv run python evaluation/run_routing_eval.py --api http://127.0.0.1:8000` | passing: 119/120, 99.17%; average route latency 2473.71 ms; fallback 22.5% |
| Performance | `uv run python evaluation/run_latency_eval.py --rounds 1` | passing: conversation 6771.90 ms, STEM 11449.75 ms, coding 9391.75 ms; route, switch, generation, RAM/VRAM/GPU recorded |
| Browser | `scripts/browser-smoke.ps1`; Playwright fixed-shell checks at 1920x1080, 1366x768, 1024x768, and 390x844 | passing; independent sidebar/message scroll, fixed footer/header/composer, mobile drawer, live stream, telemetry, Models panel, Auto new chat, and console errors 0 verified |
| Context and memory | `uv run python evaluation/run_context_stress.py --session-id <real-ui-session>` | passing: 20/20 exact prompts, 40 raw messages, historical continuity, goal/task retention, bounded summary, unique memory IDs, final implementation |
| Long conversation and recovery | 40-turn bounded unit test; 30-turn live session; backend restart; rebuild endpoint | passing: raw messages preserved, summary boundary persisted, context survived restart, rebuild rederived context |
| Router model switch | live `PUT /api/v1/models/router`, Auto chat, restore defaults | passing: route and context tasks both used the assigned `qwen3:1.7b`; defaults restored to `qwen3:0.6b` |
