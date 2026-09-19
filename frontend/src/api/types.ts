export type Mode = "auto" | "conversation" | "stem" | "coding";
export type { StreamEvent } from "./stream";

export interface SessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  preferred_mode: Mode;
}

export interface ChatMessage {
  id: number | string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  route?: string | null;
  model?: string | null;
  route_confidence?: number | null;
  route_latency_ms?: number | null;
  generation_latency_ms?: number | null;
  validation_status?: string | null;
  transient?: boolean;
}

export interface SessionDetail extends SessionSummary {
  messages: ChatMessage[];
}

export interface RouteData {
  mode: Mode;
  expert: "conversation" | "stem" | "coding";
  confidence: number;
  reason: string;
  router_model: string | null;
  latency_ms: number | null;
  routing_fallback?: boolean;
  low_confidence?: boolean;
  expert_name: string;
  expert_model: string;
  expert_model_label: string;
  session_id?: string;
}

export interface ValidationData {
  kind: string;
  status: string;
  detail?: string | null;
}

export interface MetricsData {
  route_latency_ms: number | null;
  model_switch_latency_ms: number | null;
  generation_latency_ms: number;
  total_latency_ms: number;
  model: string;
  telemetry?: SystemSnapshot;
}

export interface SystemSnapshot {
  cpu_percent: number | null;
  ram_used_bytes: number | null;
  ram_total_bytes: number | null;
  gpu_name: string | null;
  gpu_utilization_percent: number | null;
  vram_used_bytes: number | null;
  vram_total_bytes: number | null;
  backend_uptime_seconds: number | null;
  active_model: string | null;
  ollama_reachable: boolean | null;
  telemetry_available: boolean;
}
