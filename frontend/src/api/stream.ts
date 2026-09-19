export interface StreamEvent {
  type: string;
  data: Record<string, unknown>;
}

export function parseNdjsonChunk(
  chunk: string,
  remainder = "",
): { events: StreamEvent[]; remainder: string } {
  const lines = `${remainder}${chunk}`.split("\n");
  const tail = lines.pop() ?? "";
  const events: StreamEvent[] = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const parsed = JSON.parse(line) as StreamEvent;
      if (parsed?.type && parsed?.data) events.push(parsed);
    } catch {
      return { events, remainder: `${line}\n${tail}` };
    }
  }
  return { events, remainder: tail };
}

