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

