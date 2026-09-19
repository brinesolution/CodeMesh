| Area | Command/check | Status |
|---|---|---|
| Backend unit/integration/failure | `uv run pytest` | passing: 17 passed, 5 live deselected |
| Backend lint | `uv run ruff check app tests` | passing |
| Frontend typecheck/build | `npm run typecheck; npm run build` | passing |
| Frontend tests | `npm test` | passing: 9 tests |
| Live models | `scripts/verify-models.ps1`; `uv run pytest -m live -q` | passing: 4 installed, 5 live tests |
| Classroom prompts | `docs/DEMO.md` prompts through `/api/v1/chat` | passing: 6/6, exact specialist models |
| Routing | `uv run --directory backend python ../evaluation/run_routing_eval.py` | passing: 118/120, 98.33% |
| Performance | `evaluation/run_latency_eval.py --rounds 7` | passing: 21 specialist requests; route, switch, generation, RAM/VRAM/GPU recorded |
| Browser | `scripts/browser-smoke.ps1`; Playwright desktop/mobile/manual checks | passing; console errors 0; restored route/model telemetry verified |
