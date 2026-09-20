import type { Mode } from "../../../api/types";

export type MeshView = "graph" | "context" | "timeline" | "storage";
export type MeshMemoryStatus = "current" | "superseded";

export interface MeshSession {
  id: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
}

export interface MeshMessage {
  id: number;
  role: "user" | "assistant";
  content_preview: string;
  content_length: number;
  created_at: string;
  route: string | null;
  model: string | null;
  route_confidence: number | null;
  is_recent: boolean;
  is_current_prompt: boolean;
}

export interface MeshContextMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface MeshSummary {
  text: string;
  through_message_id: number | null;
  model: string | null;
  updated_at: string | null;
  message_count: number;
}

export interface MeshMemoryItem {
  id: string;
  text: string;
  source_message_id: number | null;
  updated_at: string;
  topic: string | null;
  status: MeshMemoryStatus;
}

export interface MeshMemoryHistory {
  event_id: number;
  memory_id: string;
  category: string;
  text: string;
  status: "superseded";
  source_message_id: number | null;
  replaced_by_id: string | null;
  created_at: string;
}

export interface MeshMemory {
  facts: MeshMemoryItem[];
  decisions: MeshMemoryItem[];
  constraints: MeshMemoryItem[];
  preferences: MeshMemoryItem[];
  current_goal: string | null;
  open_tasks: MeshMemoryItem[];
  topics: string[];
}

export interface MeshRecentContext {
  message_ids: number[];
  count: number;
}

export interface MeshContextPackage {
  id: number;
  expert: "conversation" | "stem" | "coding";
  expert_name: string;
  model: string;
  router_model: string | null;
  summary_included: boolean;
  summary_text: string;
  summary_through_message_id: number | null;
  memory_ids: string[];
  memory_items: MeshMemoryItem[];
  current_goal: string | null;
  recent_message_ids: number[];
  recent_messages: MeshContextMessage[];
  current_message_id: number | null;
  current_prompt: string;
  response_message_id: number | null;
  approx_context_size: number;
  context_analysis: Record<string, unknown>;
  system_prompt: string;
  created_at: string;
}

export interface MeshTimelineEvent {
  id: string;
  type: string;
  title: string;
  detail: string;
  created_at: string;
  message_id: number | null;
  node_id: string | null;
}

export interface StorageRow {
  id: string;
  values: Record<string, unknown>;
}

export interface StorageTable {
  name: string;
  columns: string[];
  row_count: number;
  rows: StorageRow[];
  truncated: boolean;
}

export interface MeshStorage {
  database: string;
  database_name: string;
  current_session_id: string;
  tables: StorageTable[];
}

export interface ContextMeshData {
  session: MeshSession;
  router: { model: string | null };
  summary: MeshSummary;
  memory: MeshMemory;
  memory_history: MeshMemoryHistory[];
  recent_context: MeshRecentContext;
  messages: MeshMessage[];
  latest_context_package: MeshContextPackage | null;
  timeline: MeshTimelineEvent[];
  storage: MeshStorage;
}

export interface ContextMeshEmptyState {
  sessionId: string | null;
  mode: Mode;
}
