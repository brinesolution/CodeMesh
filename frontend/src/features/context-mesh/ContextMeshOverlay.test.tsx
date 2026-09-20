import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ContextMeshData } from "./api/types";
import { ContextMeshOverlay } from "./ContextMeshOverlay";

const mesh: ContextMeshData = {
  session: { id: "session-1", title: "Projectile Calculator", mode: "auto", created_at: "2026-09-20T10:00:00Z", updated_at: "2026-09-20T10:10:00Z" },
  router: { model: "qwen3:0.6b" },
  summary: { text: "The user is building a projectile calculator.", through_message_id: 12, model: "qwen3:0.6b", updated_at: "2026-09-20T10:09:00Z", message_count: 12 },
  memory: { facts: [], decisions: [{ id: "language", text: "Language = Java 21", source_message_id: 8, updated_at: "2026-09-20T10:08:00Z", topic: "calculator", status: "current" }], constraints: [], preferences: [], current_goal: "Add JUnit tests", open_tasks: [], topics: ["Java"] },
  memory_history: [],
  recent_context: { message_ids: [12, 13], count: 2 },
  messages: [
    { id: 12, role: "user", content_preview: "Use Java 21.", content_length: 13, created_at: "2026-09-20T10:08:00Z", route: null, model: null, route_confidence: null, is_recent: true, is_current_prompt: false },
    { id: 13, role: "assistant", content_preview: "Java 21 is selected.", content_length: 21, created_at: "2026-09-20T10:09:00Z", route: "coding", model: "qwen2.5-coder:3b", route_confidence: 0.9, is_recent: true, is_current_prompt: false },
  ],
  latest_context_package: { id: 1, expert: "coding", expert_name: "Coding Expert", model: "qwen2.5-coder:3b", router_model: "qwen3:0.6b", summary_included: true, summary_text: "The user is building a projectile calculator.", summary_through_message_id: 12, memory_ids: ["language"], memory_items: [{ id: "language", text: "Language = Java 21", source_message_id: 8, updated_at: "2026-09-20T10:08:00Z", topic: "calculator", status: "current" }], current_goal: "Add JUnit tests", recent_message_ids: [12], recent_messages: [{ id: 12, role: "user", content: "Use Java 21.", created_at: "2026-09-20T10:08:00Z" }], current_message_id: 12, current_prompt: "Use Java 21.", response_message_id: 13, approx_context_size: 321, context_analysis: { topic: "calculator", requires_history: true, requires_summary: true, reference_detected: false, recent_turns_needed: 1 }, created_at: "2026-09-20T10:09:00Z" },
  timeline: [],
  storage: { database: "SQLite", database_name: "codemesh.db", current_session_id: "session-1", tables: [] },
};

describe("ContextMeshOverlay", () => {
  it("keeps the visualizer open while navigating its four views and closes on Escape", () => {
    const onClose = vi.fn();
    render(<ContextMeshOverlay data={mesh} loading={false} error={null} onClose={onClose} />);

    expect(screen.getByRole("heading", { name: "Context Mesh" })).toBeInTheDocument();
    expect(screen.getByText("Projectile Calculator")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Context" }));
    expect(screen.queryByText("SPECIALIST SYSTEM PROMPT")).not.toBeInTheDocument();
    expect(screen.getByText("PACKAGE INPUTS")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Timeline" }));
    expect(screen.getByRole("heading", { name: "Context timeline" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Storage" }));
    expect(screen.getByRole("heading", { name: "SQLite session mapping" })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("renders the current context package and opens a node inspector", () => {
    render(<ContextMeshOverlay data={mesh} loading={false} error={null} onClose={() => undefined} />);

    expect(screen.getByText("CONTEXT PACKAGE")).toBeInTheDocument();
    const memoryNode = document.querySelector('[data-id="memory-language"] .mesh-node');
    expect(memoryNode).not.toBeNull();
    fireEvent.click(memoryNode!);
    expect(screen.getByRole("heading", { name: "Node details" })).toBeInTheDocument();
    expect(screen.getByRole("complementary").textContent).toMatch(/decision/i);
  });
});
