import { describe, expect, it } from "vitest";

import { parseNdjsonChunk } from "./stream";

describe("parseNdjsonChunk", () => {
  it("buffers split JSON lines until a complete event arrives", () => {
    const first = parseNdjsonChunk('{"type":"token","data":{"text":"Hel', "");
    expect(first.events).toEqual([]);

    const second = parseNdjsonChunk('lo"}}\n{"type":"done","data":{}}\n', first.remainder);
    expect(second.events).toEqual([
      { type: "token", data: { text: "Hello" } },
      { type: "done", data: {} },
    ]);
    expect(second.remainder).toBe("");
  });

  it("ignores blank lines and preserves incomplete tails", () => {
    const result = parseNdjsonChunk('{"type":"status","data":{"state":"generating"}}\n\n{"type":"tok', "");
    expect(result.events).toEqual([{ type: "status", data: { state: "generating" } }]);
    expect(result.remainder).toBe('{"type":"tok');
  });
});
