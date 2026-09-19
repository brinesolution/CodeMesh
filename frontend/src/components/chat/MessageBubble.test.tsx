import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { RouteData } from "../../api/types";
import { MessageBubble } from "./MessageBubble";

const route: RouteData = {
  mode: "auto",
  expert: "stem",
  confidence: 1,
  reason: "Test route",
  router_model: "qwen3:0.6b",
  latency_ms: 10,
  expert_name: "Math & Science Expert",
  expert_model: "qwen3:1.7b",
  expert_model_label: "Qwen3 1.7B",
};

describe("MessageBubble model identity", () => {
  it("shows the persisted model beside CodeMesh after a conversation is reloaded", () => {
    const { container } = render(<MessageBubble message={{ id: 1, role: "assistant", content: "Hello", model: "smollm2:1.7b" }} />);

    expect(container.querySelector(".message-meta")?.textContent).toContain("CodeMesh");
    expect(container.querySelector(".message-meta")?.textContent).toContain("SmolLM2 1.7B");
  });

  it("uses the live route model while the assistant response is streaming", () => {
    const { container } = render(<MessageBubble message={{ id: "streaming", role: "assistant", content: "Thinking…", transient: true }} route={route} />);

    expect(container.querySelector(".message-meta")?.textContent).toContain("Math & Science Expert");
    expect(container.querySelector(".message-meta")?.textContent).toContain("Qwen3 1.7B");
  });
});
