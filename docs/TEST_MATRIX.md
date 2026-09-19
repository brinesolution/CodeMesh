| Area | Command/check | Status |
|---|---|---|
| Backend unit/integration | `uv run pytest` | passing |
| Backend lint | `uv run ruff check app tests` | passing |
| Frontend typecheck/build | `npm run typecheck; npm run build` | passing |
| Frontend tests | `npm test` | passing |
| Live models | `scripts/verify-models.ps1` + smoke prompts | pending model pulls |
| Routing | `uv run --directory backend python ../evaluation/run_routing_eval.py` | pending live run |
| Browser | desktop/mobile launch and interaction | pending live launch |

