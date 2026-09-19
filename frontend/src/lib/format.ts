export function formatBytes(value: number | null | undefined): string {
  if (value == null) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(size >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatPercent(value: number | null | undefined): string {
  return value == null ? "—" : `${Math.round(value)}%`;
}

export function modeLabel(mode: string): string {
  return ({ auto: "Auto", conversation: "Conversation", stem: "Math & Science", coding: "Coding" } as Record<string, string>)[mode] ?? mode;
}

export function modelDisplayLabel(model: string | null | undefined): string | null {
  if (!model) return null;
  return ({
    "qwen3:0.6b": "Qwen3 0.6B",
    "smollm2:1.7b": "SmolLM2 1.7B",
    "qwen3:1.7b": "Qwen3 1.7B",
    "qwen2.5-coder:3b": "Qwen2.5-Coder 3B",
  } as Record<string, string>)[model] ?? model;
}

export function expertDisplayLabel(route: string | null | undefined): string | null {
  if (!route) return null;
  return ({ conversation: "Conversation Expert", stem: "Math & Science Expert", coding: "Coding Expert" } as Record<string, string>)[route] ?? route;
}
