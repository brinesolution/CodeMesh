# Security review

Review date: 2026-09-21. Scope: tracked CodeMesh source, configuration, Git history, dependency locks, and the local release tree.

## Results

- Secret scan: pass. No credential values, private keys, bearer tokens, or real environment files were found in the release tree or reviewed history. `.env.example` contains local placeholders only.
- Dependency scan: pass. `npm audit --audit-level=moderate` and the production-only audit both report zero vulnerabilities. `npm ci --dry-run --ignore-scripts` and `uv lock --check` pass.
- CORS: pass for local v1. `backend/app/main.py:51-55` allows only the two loopback frontend origins and disables credentials.
- Context Mesh: pass. `backend/app/api/routes/context_mesh.py:8-13` serves a typed, session-scoped projection; `backend/app/context_mesh/service.py:32-373` bounds content and maps selected read-only rows. Internal specialist prompts are excluded from the public schema and UI.
- Markdown rendering: pass for the current content path. `frontend/src/components/markdown/MarkdownRenderer.tsx:58-65` skips raw HTML and uses `noreferrer noopener` for new-tab links.

## Known local-scope limitations

1. **Low — local API has no authentication.** This is intentional for the offline desktop workflow and the launch scripts bind services to `127.0.0.1`. Do not expose the API beyond the local machine without adding authentication, host validation, TLS, request limits, and a deployment-specific CORS policy.
2. **Informational — response security headers are not defined in this repository.** The Vite development server is local-only. A future public/static deployment should provide CSP, clickjacking protection, `nosniff`, referrer, and permissions headers at the serving edge.

No critical or high-severity application finding remains for the local v1 scope. This review does not authorize or implement cloud deployment.
