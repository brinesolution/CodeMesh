import type { ContextMeshData } from "./types";

const API_BASE = (import.meta.env.VITE_CODEMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function getContextMesh(sessionId: string, signal?: AbortSignal): Promise<ContextMeshData> {
  const response = await fetch(`${API_BASE}/api/v1/sessions/${encodeURIComponent(sessionId)}/mesh`, { signal });
  if (!response.ok) {
    let message = `Context Mesh request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep the stable fallback when the backend is unavailable.
    }
    throw new Error(message);
  }
  return (await response.json()) as ContextMeshData;
}
