import { MarkerType, type Edge, type Node } from "@xyflow/react";

import type { ContextMeshData, MeshMemoryItem, MeshView } from "../api/types";

export type GraphFilter = "messages" | "summary" | "memory" | "router" | "context" | "storage";

export type InspectorField = [label: string, value: string];

export interface NodeInspectorData {
  type: string;
  title: string;
  fields: InspectorField[];
  sourceMessageId?: number | null;
}

export interface MeshNodeData extends Record<string, unknown> {
  kind: string;
  eyebrow: string;
  title: string;
  detail: string;
  accent: string;
  active?: boolean;
  status?: string;
  preview: string;
  inspector: NodeInspectorData;
  searchMatch?: boolean;
}

export type MeshNode = Node<MeshNodeData>;
export type MeshEdge = Edge;

interface BuildOptions {
  filters: Record<GraphFilter, boolean>;
  showSuperseded: boolean;
  search: string;
}

const palette = {
  cyan: "#49c5ff",
  violet: "#a88bff",
  blue: "#68a8ff",
  slate: "#8fa3b8",
  amber: "#ffc467",
  green: "#56db9b",
};

export function buildContextGraph(data: ContextMeshData, options: BuildOptions): { nodes: MeshNode[]; edges: MeshEdge[] } {
  const nodes: MeshNode[] = [];
  const edges: MeshEdge[] = [];
  const visible = new Set<string>();
  const query = options.search.trim().toLowerCase();

  const addNode = (node: MeshNode, filter: GraphFilter) => {
    if (!options.filters[filter]) return;
    const matches = !query || nodeSearchText(node).includes(query);
    nodes.push({ ...node, data: { ...node.data, searchMatch: Boolean(query && matches) } });
    visible.add(node.id);
  };
  const addEdge = (source: string, target: string, label?: string, active = false) => {
    if (!visible.has(source) || !visible.has(target)) return;
    edges.push({
      id: `${source}-${target}`,
      source,
      target,
      type: "smoothstep",
      animated: active,
      label,
      className: active ? "mesh-edge-active" : "mesh-edge",
      markerEnd: { type: MarkerType.ArrowClosed, color: active ? palette.cyan : "#52657a" },
    });
  };

  addNode(card("session", "CURRENT CHAT", data.session.title, `${data.session.mode.toUpperCase()} · ${shortId(data.session.id)}`, palette.cyan, {
    type: "Session",
    title: data.session.title,
    fields: [
      ["Mode", data.session.mode],
      ["Session", data.session.id],
      ["Created", formatDate(data.session.created_at)],
      ["Updated", formatDate(data.session.updated_at)],
    ],
  }), "context");

  addNode(card("router", "ROUTER", data.router.model ?? "Configured default", "Routing + context analysis", palette.violet, {
    type: "Router",
    title: data.router.model ?? "Router not used yet",
    fields: [["Model", data.router.model ?? "Not recorded"], ["Role", "Route and context intelligence"]],
  }), "router");

  addNode(card("summary", "ROLLING SUMMARY", data.summary.text ? compact(data.summary.text, 120) : "Not generated yet", data.summary.text ? `Through message #${data.summary.through_message_id ?? "—"}` : "Awaiting enough conversation", palette.violet, {
    type: "Summary",
    title: "Rolling summary",
    fields: [
      ["Text", data.summary.text || "Not generated yet"],
      ["Coverage", data.summary.message_count ? `${data.summary.message_count} messages` : "No messages covered"],
      ["Model", data.summary.model ?? "Not recorded"],
      ["Through", data.summary.through_message_id ? `Message #${data.summary.through_message_id}` : "Not generated"],
    ],
  }), "summary");

  const rawHistoryId = "raw-history";
  addNode(card(rawHistoryId, "RAW HISTORY", `${data.messages.length} messages`, data.messages.some((message) => message.is_recent) ? "Older history is dimmed · recent context is bright" : "No recent context recorded", palette.blue, {
    type: "Raw history",
    title: "Conversation history",
    fields: [["Messages shown", String(data.messages.length)], ["Recent active", String(data.recent_context.count)]],
  }), "messages");

  const messageNodes = createMessageNodes(data, options, addNode);
  messageNodes.forEach((messageNode) => addEdge(rawHistoryId, messageNode));

  const memoryRoot = "memory-root";
  addNode(card(memoryRoot, "STRUCTURED MEMORY", `${memoryCount(data)} active items`, data.memory.current_goal ? "Current goal is pinned" : "No current goal", palette.green, {
    type: "Structured memory",
    title: "Structured memory",
    fields: [["Active items", String(memoryCount(data))], ["Topics", String(data.memory.topics.length)], ["History", `${data.memory_history.length} superseded`]],
  }), "memory");
  const memoryNodes = createMemoryNodes(data, options, addNode);
  memoryNodes.forEach((memoryNode) => addEdge(memoryRoot, memoryNode));

  const recentId = "recent-context";
  addNode(card(recentId, "ACTIVE CONTEXT", `${data.recent_context.count} recent messages`, "Eligible for direct specialist context", palette.cyan, {
    type: "Recent context",
    title: "Active recent context",
    fields: [["Message IDs", data.recent_context.message_ids.map((id) => `#${id}`).join(", ") || "None"], ["Window", `${data.recent_context.count} messages`]],
  }, true), "context");

  const packageData = data.latest_context_package;
  const packageId = packageData ? `context-package-${packageData.id}` : "context-package-empty";
  addNode(card(packageId, "CONTEXT PACKAGE", packageData ? `${packageData.expert_name} · ${packageData.model}` : "No package recorded yet", packageData ? `${packageData.memory_items.length} memory · ${packageData.recent_message_ids.length} recent${packageData.summary_included ? " · summary" : ""}` : "The next request will appear here", palette.cyan, {
    type: "Context package",
    title: "Latest assembled context",
    fields: packageData ? [
      ["Expert", packageData.expert_name],
      ["Model", packageData.model],
      ["Summary", packageData.summary_included ? "Included" : "Not included"],
      ["Memory items", String(packageData.memory_items.length)],
      ["Recent messages", String(packageData.recent_message_ids.length)],
      ["Approx. size", `${packageData.approx_context_size} chars`],
    ] : [["Status", "No persisted context run yet"]],
  }, Boolean(packageData)), "context");

  const expert = packageData?.expert ?? latestExpert(data);
  const expertModel = packageData?.model ?? latestModel(data);
  const expertId = `expert-${expert}`;
  addNode(card(expertId, "SELECTED EXPERT", expert ? expertLabel(expert) : "Not selected", expertModel ?? "Awaiting a response", expert === "coding" ? palette.blue : expert === "stem" ? palette.violet : palette.cyan, {
    type: "Expert",
    title: expert ? expertLabel(expert) : "No specialist selected",
    fields: [["Expert", expert ? expertLabel(expert) : "Not recorded"], ["Model", expertModel ?? "Not recorded"]],
  }, Boolean(packageData)), "context");
  if (expertModel) {
    addNode(card(`model-${expertModel}`, "SPECIALIST MODEL", expertModel, "Latest generation model", palette.blue, {
      type: "Model",
      title: expertModel,
      fields: [["Assigned specialist", expert ? expertLabel(expert) : "Not recorded"], ["Source", "Latest context package"]],
    }, Boolean(packageData)), "context");
    addEdge(expertId, `model-${expertModel}`, "generated by", Boolean(packageData));
  }

  const dbId = "database";
  addNode(card(dbId, "SQLITE", data.storage.database_name, "Read-only current-session storage", palette.slate, {
    type: "Database",
    title: data.storage.database_name,
    fields: [["Engine", data.storage.database], ["Session", data.storage.current_session_id], ["Tables", String(data.storage.tables.length)]],
  }), "storage");
  const tableNodes = data.storage.tables.map((table, index) => {
    const id = `table-${table.name}`;
    addNode(card(id, "TABLE", table.name, `${table.row_count} row${table.row_count === 1 ? "" : "s"}`, palette.slate, {
      type: "SQLite table",
      title: table.name,
      fields: [["Columns", table.columns.join(", ")], ["Rows", String(table.row_count)], ["Current session", data.storage.current_session_id]],
    }), "storage");
    return id;
  });
  tableNodes.forEach((tableId) => addEdge(dbId, tableId, "stores"));

  addEdge("session", "router", "interpreted by", true);
  addEdge("session", rawHistoryId, "contains");
  addEdge("session", memoryRoot, "remembers");
  addEdge("router", "summary", "summarized into");
  addEdge("router", memoryRoot, "updates");
  addEdge(rawHistoryId, "summary", data.summary.text ? "summarized into" : undefined);
  addEdge(rawHistoryId, recentId, "recent window");
  addEdge("summary", packageId, "included in", Boolean(packageData?.summary_included));
  addEdge(memoryRoot, packageId, "included in", Boolean(packageData && packageData.memory_items.length > 0));
  addEdge(recentId, packageId, "included in", Boolean(packageData && packageData.recent_message_ids.length > 0));
  addEdge(packageId, expertId, "routed to", Boolean(packageData));
  addEdge("session", dbId, "stored in");
  addEdge(rawHistoryId, "table-messages", "stored in");
  addEdge(memoryRoot, "table-session_context", "stored in");
  addEdge(packageId, "table-context_runs", "stored in");

  return { nodes, edges };
}

function createMessageNodes(data: ContextMeshData, options: BuildOptions, addNode: (node: MeshNode, filter: GraphFilter) => void): string[] {
  const messages = data.messages;
  const directStart = messages.length > 40 ? Math.max(0, messages.length - 12) : 0;
  const ids: string[] = [];
  if (directStart > 0) {
    for (let index = 0; index < directStart; index += 20) {
      const group = messages.slice(index, Math.min(index + 20, directStart));
      const id = `message-group-${index + 1}`;
      addNode(card(id, "MESSAGE GROUP", `Messages #${group[0]?.id}–#${group[group.length - 1]?.id}`, `${group.length} older messages · expand in Storage`, palette.blue, {
        type: "Message group",
        title: `Messages #${group[0]?.id}–#${group[group.length - 1]?.id}`,
        fields: [["Count", String(group.length)], ["Status", "Older history"]],
      }), "messages");
      ids.push(id);
    }
  }
  messages.slice(directStart).forEach((message, index) => {
    const id = `message-${message.id}`;
    const expert = message.route ? expertLabel(message.route) : message.role === "user" ? "Current prompt" : "Assistant";
    addNode(card(id, message.role === "user" ? "USER MESSAGE" : "ASSISTANT MESSAGE", `#${message.id} · ${expert}`, message.content_preview, message.is_recent ? palette.cyan : palette.blue, {
      type: message.role === "user" ? "User message" : "Assistant message",
      title: `Message #${message.id}`,
      fields: [
        ["Role", message.role],
        ["Expert", message.route ? expertLabel(message.route) : "—"],
        ["Model", message.model ?? "—"],
        ["Created", formatDate(message.created_at)],
        ["Content", message.content_preview],
        ["Status", message.is_recent ? "Active recent context" : "Older history"],
      ],
    }, message.is_recent || message.is_current_prompt), "messages");
    ids.push(id);
  });
  return ids;
}

function createMemoryNodes(data: ContextMeshData, options: BuildOptions, addNode: (node: MeshNode, filter: GraphFilter) => void): string[] {
  const nodes: string[] = [];
  const groups: Array<[string, string, MeshMemoryItem[]]> = [
    ["facts", "FACTS", data.memory.facts],
    ["decisions", "DECISIONS", data.memory.decisions],
    ["constraints", "CONSTRAINTS", data.memory.constraints],
    ["preferences", "PREFERENCES", data.memory.preferences],
    ["open_tasks", "OPEN TASKS", data.memory.open_tasks],
  ];
  groups.forEach(([category, label, items]) => {
    if (!items.length) return;
    const groupId = `memory-group-${category}`;
    addNode(card(groupId, "MEMORY GROUP", label, `${items.length} current item${items.length === 1 ? "" : "s"}`, palette.green, {
      type: "Memory group",
      title: label,
      fields: [["Category", label], ["Current items", String(items.length)]],
    }), "memory");
    nodes.push(groupId);
    items.forEach((item) => {
      const id = `memory-${item.id}`;
      addNode(card(id, label.slice(0, -1), compact(item.text, 100), item.status === "current" ? "Current" : "Superseded", item.status === "current" ? palette.green : palette.slate, {
        type: label.slice(0, -1),
        title: item.text,
        fields: [["Status", item.status === "current" ? "Current" : "Superseded"], ["Source", item.source_message_id ? `Message #${item.source_message_id}` : "Not recorded"], ["Topic", item.topic ?? "—"], ["Updated", formatDate(item.updated_at)]],
        sourceMessageId: item.source_message_id,
      }, item.status === "current"), "memory");
      nodes.push(id);
    });
  });
  if (data.memory.current_goal) {
    const id = "current-goal";
    addNode(card(id, "CURRENT GOAL", compact(data.memory.current_goal, 110), "Pinned shared objective", palette.amber, {
      type: "Current goal",
      title: data.memory.current_goal,
      fields: [["Status", "Current"], ["Stored in", "session_context.memory_json"]],
    }, true), "memory");
    nodes.push(id);
  }
  data.memory.topics.slice(0, 8).forEach((topic, index) => {
    const id = `topic-${index}`;
    addNode(card(id, "TOPIC", topic, "Structured topic", palette.green, {
      type: "Topic",
      title: topic,
      fields: [["Source", "Structured memory"], ["Status", "Current"]],
    }), "memory");
    nodes.push(id);
  });
  if (options.showSuperseded) {
    data.memory_history.forEach((item) => {
      const id = `memory-history-${item.event_id}`;
      addNode(card(id, "SUPERSEDED", compact(item.text, 100), `Replaced by ${item.replaced_by_id ? "current value" : "later state"}`, palette.slate, {
        type: "Superseded memory",
        title: item.text,
        fields: [["Category", item.category], ["Status", "Superseded"], ["Source", item.source_message_id ? `Message #${item.source_message_id}` : "Not recorded"]],
        sourceMessageId: item.source_message_id,
      }), "memory");
      nodes.push(id);
    });
  }
  return nodes;
}

function card(id: string, eyebrow: string, title: string, detail: string, accent: string, inspector: NodeInspectorData, active = false): MeshNode {
  return {
    id,
    type: "mesh",
    position: positionFor(id),
    data: { kind: id.split("-")[0], eyebrow, title, detail, accent, active, preview: `${eyebrow} · ${title}\n${detail}`, inspector },
  };
}

function positionFor(id: string): { x: number; y: number } {
  if (id === "session") return { x: 30, y: 250 };
  if (id === "router") return { x: 300, y: 70 };
  if (id === "raw-history") return { x: 300, y: 260 };
  if (id === "memory-root") return { x: 300, y: 520 };
  if (id === "summary") return { x: 620, y: 40 };
  if (id === "recent-context") return { x: 620, y: 270 };
  if (id.startsWith("message")) return { x: 620, y: 420 + (numericTail(id) % 7) * 90 };
  if (id.startsWith("memory-group")) return { x: 620, y: 520 + (numericTail(id) % 5) * 110 };
  if (id.startsWith("memory-") || id === "current-goal" || id.startsWith("topic-")) return { x: 950, y: 120 + (numericTail(id) % 10) * 95 };
  if (id.startsWith("context-package")) return { x: 1250, y: 260 };
  if (id.startsWith("expert-")) return { x: 1550, y: 260 };
  if (id.startsWith("model-")) return { x: 1830, y: 260 };
  if (id === "database") return { x: 1250, y: 650 };
  if (id.startsWith("table-")) return { x: 1550, y: 570 + (numericTail(id) % 5) * 90 };
  return { x: 950, y: 650 };
}

function numericTail(value: string): number {
  const parsed = Number(value.match(/(\d+)$/)?.[1] ?? 0);
  return Number.isFinite(parsed) ? parsed : value.length;
}

function nodeSearchText(node: MeshNode): string {
  return `${node.data.eyebrow} ${node.data.title} ${node.data.detail} ${node.data.inspector.fields.map((field) => `${field[0]} ${field[1]}`).join(" ")}`.toLowerCase();
}

function memoryCount(data: ContextMeshData): number {
  return data.memory.facts.length + data.memory.decisions.length + data.memory.constraints.length + data.memory.preferences.length + data.memory.open_tasks.length + (data.memory.current_goal ? 1 : 0);
}

function latestExpert(data: ContextMeshData): string | null {
  return [...data.messages].reverse().find((message) => message.role === "assistant" && message.route)?.route ?? null;
}

function latestModel(data: ContextMeshData): string | null {
  return [...data.messages].reverse().find((message) => message.role === "assistant" && message.model)?.model ?? null;
}

function expertLabel(value: string): string {
  return value === "stem" ? "Math & Science Expert" : value === "coding" ? "Coding Expert" : "Conversation Expert";
}

function compact(value: string, limit: number): string {
  const text = value.replace(/\s+/g, " ").trim();
  return text.length <= limit ? text : `${text.slice(0, limit - 1).trimEnd()}…`;
}

function shortId(id: string): string {
  return id.slice(0, 8);
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
