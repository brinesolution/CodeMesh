export type Mode = "auto" | "conversation" | "stem" | "coding";
export type ModelRole = "router" | "conversation" | "stem" | "coding";
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
  confidence: number | null;
  reason: string;
  router_model: string | null;
  latency_ms: number | null;
  routing_fallback?: boolean;
  low_confidence?: boolean;
  expert_name: string;
  expert_model: string;
  expert_model_label: string;
  session_id?: string;
  topic?: string | null;
  context_router_model?: string | null;
  context_latency_ms?: number | null;
  context_fallback?: boolean;
  requires_history?: boolean;
  requires_summary?: boolean;
  reference_detected?: boolean;
  recent_turns_needed?: number;
}

export interface ValidationData {
  kind: string;
  status: string;
  detail?: string | null;
}

export interface MetricsData {
  route_latency_ms: number | null;
  model_switch_latency_ms: number | null;
  generation_latency_ms: number | null;
  total_latency_ms: number | null;
  specialist_generation_latency_ms?: number | null;
  routing_context_latency_ms?: number | null;
  memory_update_latency_ms?: number | null;
  summary_update_latency_ms?: number | null;
  model: string;
  context?: ContextGenerationMetadata;
  telemetry?: SystemSnapshot;
}

export interface ContextGenerationMetadata {
  session_id: string;
  mode: Mode;
  expert: "conversation" | "stem" | "coding";
  router_model: string | null;
  specialist_model: string;
  recent_message_count: number;
  recent_message_roles: string[];
  summary_included: boolean;
  structured_memory_included: boolean;
  memory_item_count: number;
  context_analysis: {
    topic: string | null;
    requires_history: boolean;
    requires_summary: boolean;
    reference_detected: boolean;
    recent_turns_needed: number;
  };
  route_confidence: number | null;
  context_analysis_latency_ms: number;
  memory_update_status: string;
  summary_update_status: string;
  memory_model: string | null;
  summary_model: string | null;
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

export interface InstalledModel {
  name: string;
  size_bytes: number | null;
  digest: string | null;
}

export interface ModelRoleConfig {
  key: ModelRole;
  model: string;
  label: string;
  role: "routing" | "expert";
  installed: boolean;
}

export interface ModelConfiguration {
  ollama_reachable: boolean;
  available_models: InstalledModel[];
  models: ModelRoleConfig[];
  assignments: Record<ModelRole, string>;
  defaults: Record<ModelRole, string>;
  active_model: string | null;
}

export interface MemoryItem {
  id: string;
  text: string;
  source_message_id: number | null;
  updated_at: string;
  topic: string | null;
}

export interface StructuredMemory {
  facts: MemoryItem[];
  decisions: MemoryItem[];
  constraints: MemoryItem[];
  preferences: MemoryItem[];
  current_goal: string | null;
  open_tasks: MemoryItem[];
  topics: string[];
}

export interface SessionContext {
  summary: string;
  memory: StructuredMemory;
  recent_context_turns: number;
  summary_through_message_id: number | null;
  current_topic: string | null;
  last_updated: string | null;
  version: number;
  router_model: string | null;
  last_memory_model: string | null;
  last_summary_model: string | null;
}

export interface ContextIntelligenceSettings {
  shared_context_enabled: boolean;
  recent_context_enabled: boolean;
  structured_memory_enabled: boolean;
  rolling_summary_enabled: boolean;
  reference_resolution_enabled: boolean;
  smart_context_analysis_enabled: boolean;
  historical_changes_enabled: boolean;
}

export interface ContextSettingsResponse extends ContextIntelligenceSettings {
  effective: ContextIntelligenceSettings;
}
