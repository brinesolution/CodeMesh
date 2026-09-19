import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ModelConfiguration } from "../../api/types";
import { ModelConfigurationPanel } from "./ModelConfigurationPanel";

const configuration: ModelConfiguration = {
  ollama_reachable: true,
  available_models: [
    { name: "qwen3:0.6b", size_bytes: 600, digest: null },
    { name: "smollm2:1.7b", size_bytes: 1700, digest: null },
    { name: "qwen3:1.7b", size_bytes: 1700, digest: null },
    { name: "qwen2.5-coder:3b", size_bytes: 3000, digest: null },
    { name: "phi4-mini", size_bytes: 4000, digest: null },
  ],
  models: [],
  assignments: {
    router: "qwen3:0.6b",
    conversation: "smollm2:1.7b",
    stem: "qwen3:1.7b",
    coding: "qwen2.5-coder:3b",
  },
  defaults: {
    router: "qwen3:0.6b",
    conversation: "smollm2:1.7b",
    stem: "qwen3:1.7b",
    coding: "qwen2.5-coder:3b",
  },
  active_model: null,
};

describe("ModelConfigurationPanel", () => {
  it("renders live model choices for each role and emits assignments", () => {
    const onAssign = vi.fn();
    render(<ModelConfigurationPanel configuration={configuration} error={null} loading={false} savingRole={null} resetting={false} onRefresh={vi.fn()} onAssign={onAssign} onReset={vi.fn()} />);

    expect(screen.getByLabelText("Router model")).toBeInTheDocument();
    expect(screen.getAllByRole("option", { name: "phi4-mini" })).toHaveLength(4);
    fireEvent.change(screen.getByLabelText("Coding model"), { target: { value: "phi4-mini" } });

    expect(onAssign).toHaveBeenCalledWith("coding", "phi4-mini");
  });
});
