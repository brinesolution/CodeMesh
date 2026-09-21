import type { ContextIntelligenceSettings, ContextSettingsResponse, Mode, ModelConfiguration, ModelRole, SessionContext, SessionDetail, SessionSummary, StreamEvent, SystemSnapshot } from "./types";
import { getContextMesh } from "../features/context-mesh/api/contextMeshApi";
import { parseNdjsonChunk } from "./stream";

const API_BASE = (import.meta.env.VITE_CODEMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep the stable fallback when the backend is unavailable.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const api = {
  listSessions: () => request<SessionSummary[]>("/sessions"),
  getSession: (id: string) => request<SessionDetail>(`/sessions/${id}`),
  createSession: (preferredMode: Mode = "auto", title = "New chat") =>
    request<SessionSummary>("/sessions", {
      method: "POST",
      body: JSON.stringify({ preferred_mode: preferredMode, title }),
    }),
  deleteSession: (id: string) => request<{ deleted: boolean }>(`/sessions/${id}`, { method: "DELETE" }),
  system: () => request<SystemSnapshot>("/system"),
  listModels: () => request<ModelConfiguration>("/models"),
  assignModel: (role: ModelRole, model: string) =>
    request<ModelConfiguration>(`/models/${role}`, {
      method: "PUT",
      body: JSON.stringify({ model }),
    }),
  resetModels: () => request<ModelConfiguration>("/models/reset", { method: "POST" }),
  getSessionContext: (id: string) => request<SessionContext>(`/sessions/${id}/context`),
  getContextSettings: () => request<ContextSettingsResponse>("/settings/context"),
  updateContextSettings: (patch: Partial<ContextIntelligenceSettings>) =>
    request<ContextSettingsResponse>("/settings/context", {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  resetContextSettings: () => request<ContextSettingsResponse>("/settings/context/reset", { method: "POST" }),
  getContextMesh,
};

export async function streamChat(
  input: { message: string; mode: Mode; sessionId?: string },
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: input.message, mode: input.mode, session_id: input.sessionId }),
  });
  if (!response.ok || !response.body) {
    throw new Error(response.ok ? "The local stream was empty." : `Chat request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let remainder = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const parsed = parseNdjsonChunk(decoder.decode(value, { stream: true }), remainder);
      remainder = parsed.remainder;
      parsed.events.forEach(onEvent);
    }
    const final = parseNdjsonChunk(decoder.decode(), remainder);
    final.events.forEach(onEvent);
  } finally {
    reader.releaseLock();
  }
}
