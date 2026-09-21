import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ContextSettingsResponse } from "../../api/types";
import { ContextIntelligenceSettings } from "./ContextIntelligenceSettings";

const defaults: ContextSettingsResponse = {
  shared_context_enabled: true,
  recent_context_enabled: true,
  structured_memory_enabled: true,
  rolling_summary_enabled: true,
  reference_resolution_enabled: true,
  smart_context_analysis_enabled: true,
  historical_changes_enabled: true,
  effective: {
    shared_context_enabled: true,
    recent_context_enabled: true,
    structured_memory_enabled: true,
    rolling_summary_enabled: true,
    reference_resolution_enabled: true,
    smart_context_analysis_enabled: true,
    historical_changes_enabled: true,
  },
};

describe("ContextIntelligenceSettings", () => {
  it("renders every persisted context control enabled by default", () => {
    render(<ContextIntelligenceSettings settings={defaults} loading={false} error={null} savingKey={null} resetting={false} onRefresh={vi.fn()} onToggle={vi.fn()} onReset={vi.fn()} />);

    for (const label of ["Shared Context", "Recent Conversation", "Structured Memory", "Rolling Summary", "Reference Resolution", "Smart Context Analysis", "Historical Changes"]) {
      expect(screen.getByRole("switch", { name: label })).toBeChecked();
    }
  });

  it("shows child preferences as ineffective while retaining their stored values", () => {
    const settings = { ...defaults, shared_context_enabled: false, effective: { ...defaults.effective, shared_context_enabled: false, recent_context_enabled: false, structured_memory_enabled: false, rolling_summary_enabled: false, reference_resolution_enabled: false, smart_context_analysis_enabled: false, historical_changes_enabled: false } };
    render(<ContextIntelligenceSettings settings={settings} loading={false} error={null} savingKey={null} resetting={false} onRefresh={vi.fn()} onToggle={vi.fn()} onReset={vi.fn()} />);

    expect(screen.getByRole("switch", { name: "Structured Memory" })).toBeChecked();
    expect(screen.getByText("Shared Context is off. Child preferences are retained but currently ineffective.")).toBeInTheDocument();
    expect(screen.getAllByText("OFF", { selector: ".context-toggle-state" })).toHaveLength(7);
  });

  it("emits backend setting changes and restore defaults", () => {
    const onToggle = vi.fn();
    const onReset = vi.fn();
    render(<ContextIntelligenceSettings settings={defaults} loading={false} error={null} savingKey={null} resetting={false} onRefresh={vi.fn()} onToggle={onToggle} onReset={onReset} />);

    fireEvent.click(screen.getByRole("switch", { name: "Rolling Summary" }));
    fireEvent.click(screen.getByRole("button", { name: "Restore Context Defaults" }));
    expect(onToggle).toHaveBeenCalledWith("rolling_summary_enabled", false);
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
