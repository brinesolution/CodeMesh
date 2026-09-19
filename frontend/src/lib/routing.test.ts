import { describe, expect, it } from "vitest";

import type { ChatMessage } from "../api/types";
import { latestAssistantMessage, metricsDataFromMessage, routeDataFromMessage, ROUTING_MODE_OPTIONS } from "./routing";

const assistant: ChatMessage = {
  id: 2,
  role: "assistant",
  content: "Cloud computing explanation",
  route: "conversation",
  model: "smollm2:1.7b",
  route_confidence: 0.93,
  route_latency_ms: 812,
  generation_latency_ms: 2400,
  validation_status: "not_applicable",
};

describe("restored routing trace", () => {
  it("reconstructs route and metrics from a persisted assistant message", () => {
    const route = routeDataFromMessage(assistant, "auto", undefined, "session-1");
    const metrics = metricsDataFromMessage(assistant);

    expect(route).toMatchObject({
      mode: "auto",
      expert: "conversation",
      router_model: "qwen3:0.6b",
      confidence: 0.93,
      latency_ms: 812,
      expert_model_label: "SmolLM2 1.7B",
      session_id: "session-1",
    });
    expect(metrics).toMatchObject({ model: "smollm2:1.7b", route_latency_ms: 812, generation_latency_ms: 2400 });
  });

  it("keeps the route choices explicit and finds the latest assistant response", () => {
    expect(ROUTING_MODE_OPTIONS).toEqual(["auto", "conversation", "stem", "coding"]);
    expect(latestAssistantMessage([{ ...assistant, id: 1, role: "user" }, assistant])?.id).toBe(2);
  });

  it("restores a manual route from its zero-latency trace", () => {
    const route = routeDataFromMessage({ ...assistant, route: "coding", model: "qwen2.5-coder:3b", route_confidence: 1, route_latency_ms: 0 }, "auto");

    expect(route).toMatchObject({ mode: "coding", router_model: null, expert: "coding" });
  });
});
