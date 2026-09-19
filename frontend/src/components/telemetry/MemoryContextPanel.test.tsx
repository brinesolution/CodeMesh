import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { SessionContext } from "../../api/types";
import { MemoryContextPanel } from "./MemoryContextPanel";

const context: SessionContext = {
  summary: "The user is building a local Java projectile calculator.",
  memory: {
    facts: [
      {
        id: "gravity",
        text: "Gravity is 9.81 m/s².",
        source_message_id: 1,
        updated_at: "2026-09-20T10:00:00Z",
        topic: "physics",
      },
    ],
    decisions: [
      {
        id: "language",
        text: "Use Java 21.",
        source_message_id: 2,
        updated_at: "2026-09-20T10:01:00Z",
        topic: "implementation",
      },
    ],
    constraints: [
      {
        id: "offline",
        text: "The application must work offline.",
        source_message_id: 3,
        updated_at: "2026-09-20T10:02:00Z",
        topic: "runtime",
      },
    ],
    preferences: [],
    current_goal: "Implement input validation.",
    open_tasks: [
      {
        id: "tests",
        text: "Add unit tests.",
        source_message_id: 4,
        updated_at: "2026-09-20T10:03:00Z",
        topic: "quality",
      },
    ],
    topics: ["projectile motion", "Java"],
  },
  recent_context_turns: 6,
  summary_through_message_id: 12,
  current_topic: "projectile calculator",
  last_updated: "2026-09-20T10:03:00Z",
  version: 3,
  router_model: "qwen3:0.6b",
  last_memory_model: "qwen3:0.6b",
  last_summary_model: "qwen3:0.6b",
};

describe("MemoryContextPanel", () => {
  it("shows inspectable shared context without internal prompt content", () => {
    render(
      <MemoryContextPanel
        sessionId="session-1"
        context={context}
        loading={false}
        error={null}
        onRefresh={vi.fn()}
      />,
    );

    expect(screen.getByText(context.summary)).toBeInTheDocument();
    expect(screen.getByText("Implement input validation.")).toBeInTheDocument();
    expect(screen.getByText("Use Java 21.")).toBeInTheDocument();
    expect(screen.getByText("The application must work offline.")).toBeInTheDocument();
    expect(screen.getByText("projectile motion · Java")).toBeInTheDocument();
    expect(screen.queryByText(/chain.of.thought|scratchpad|system prompt/i)).not.toBeInTheDocument();
  });

  it("explains when there is no active chat", () => {
    render(
      <MemoryContextPanel
        sessionId={null}
        context={null}
        loading={false}
        error={null}
        onRefresh={vi.fn()}
      />,
    );

    expect(screen.getByText("Select or start a chat to inspect its shared context.")).toBeInTheDocument();
  });
});
