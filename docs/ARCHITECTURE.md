# Architecture

CodeMesh keeps the local request path modular:

```text
React chat
   ↓ HTTP / NDJSON
FastAPI routes
   ↓
Orchestrator ── RouterService ── ModelRegistry ── Ollama gateway
   │
   ├─ Context Intelligence → summaries and structured memory
   ├─ Specialist registry → Conversation / STEM / Coding prompts
   └─ ChatRepository → SQLite sessions, messages, context, and audit rows
```

The `ModelRegistry` is the single source for role assignments. The router and context services resolve the current Router model at request time; the orchestrator resolves the active specialist model through the same registry. The Models panel reads the local Ollama catalog and validates assignments before changing them.

The frontend is an explicit fixed-height shell. Sidebar history and the main message list own independent scroll regions, while the header, sidebar status/footer, and composer remain visible. Streaming uses NDJSON over `fetch`, so the local UI does not require WebSockets.

Context Mesh is a read-only, session-scoped projection. The backend bounds message content and context-run history, returns selected semantic metadata, and maps storage rows without accepting SQL or file paths. The frontend owns graph coordinates and presentation.

The local SQLite schema is created by `Base.metadata.create_all` on startup. Raw messages remain the recovery source; summaries, memory, and context-run records are additive derived state. Docker/AWS seams are documented separately and are not part of local v1.
