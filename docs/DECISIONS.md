- 2026-09-19: Use `uv` + npm because uv is installed and pnpm is not; keep the code Python 3.12-compatible while running on available Python 3.13.
- 2026-09-19: Use NDJSON streaming over standard fetch; it keeps the stable event contract and handles split chunks without WebSockets.
- 2026-09-19: Ollama lifecycle unloads the previous specialist on route switches while keeping the router warm via keep-alive.

