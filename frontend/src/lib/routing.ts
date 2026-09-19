import type { ChatMessage, MetricsData, Mode, RouteData, ValidationData } from "../api/types";
import { expertDisplayLabel, modelDisplayLabel } from "./format";

export const ROUTER_MODEL = "qwen3:0.6b";
export const ROUTING_MODE_OPTIONS: readonly Mode[] = ["auto", "conversation", "stem", "coding"];

const expertRoutes = new Set<NonNullable<ChatMessage["route"]>>(["conversation", "stem", "coding"]);

function isExpertRoute(route: string | null | undefined): route is RouteData["expert"] {
  return route != null && expertRoutes.has(route);
}

export function latestAssistantMessage(messages: ChatMessage[]) {
  return [...messages].reverse().find((message) => message.role === "assistant");
}

export function routeDataFromMessage(
  message: ChatMessage | undefined,
  preferredMode: Mode,
  fallback?: RouteData,
  sessionId?: string,
): RouteData | undefined {
  if (!message || message.role !== "assistant") return fallback;
  if (!isExpertRoute(message.route) || !message.model) return fallback;

  // Manual routes are persisted with zero routing latency and full confidence.
  // This lets mixed-mode sessions restore the correct trace without guessing from
  // the session's original preferred mode.
  const isPersistedManualRoute = message.route_latency_ms === 0 && message.route_confidence === 1;
  const restoredMode: Mode = isPersistedManualRoute ? message.route : message.route_latency_ms != null ? "auto" : preferredMode;

  return {
    mode: restoredMode,
    expert: message.route,
    confidence: message.route_confidence ?? null,
    reason: restoredMode === "auto" ? "Restored from the saved Auto route." : "Manual specialist selection recorded with the response.",
    router_model: restoredMode === "auto" ? ROUTER_MODEL : null,
    latency_ms: message.route_latency_ms ?? null,
    routing_fallback: false,
    low_confidence: false,
    expert_name: expertDisplayLabel(message.route) ?? message.route,
    expert_model: message.model,
    expert_model_label: modelDisplayLabel(message.model) ?? message.model,
    session_id: sessionId,
  };
}

export function metricsDataFromMessage(message: ChatMessage | undefined, fallback?: MetricsData): MetricsData | undefined {
  const model = message?.model ?? fallback?.model;
  if (!model) return fallback;
  return {
    route_latency_ms: message?.route_latency_ms ?? fallback?.route_latency_ms ?? null,
    model_switch_latency_ms: fallback?.model_switch_latency_ms ?? null,
    generation_latency_ms: message?.generation_latency_ms ?? fallback?.generation_latency_ms ?? null,
    total_latency_ms: fallback?.total_latency_ms ?? message?.generation_latency_ms ?? null,
    model,
    telemetry: fallback?.telemetry,
  };
}

export function validationDataFromMessage(message: ChatMessage | undefined, fallback?: ValidationData): ValidationData | undefined {
  if (!message?.validation_status) return fallback;
  const kind = message.route === "coding" ? "code" : message.route === "stem" ? "stem" : "none";
  return { kind, status: message.validation_status, detail: message.validation_status === "valid" ? "Recorded as valid." : undefined };
}
