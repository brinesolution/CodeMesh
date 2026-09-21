import { RefreshCw, RotateCcw } from "lucide-react";

import type { ContextIntelligenceSettings, ContextSettingsResponse } from "../../api/types";

interface Props {
  settings: ContextSettingsResponse | null;
  loading: boolean;
  error: string | null;
  savingKey: keyof ContextIntelligenceSettings | null;
  resetting: boolean;
  onRefresh: () => void;
  onToggle: (key: keyof ContextIntelligenceSettings, value: boolean) => void;
  onReset: () => void;
}

const DEFAULTS: ContextIntelligenceSettings = {
  shared_context_enabled: true,
  recent_context_enabled: true,
  structured_memory_enabled: true,
  rolling_summary_enabled: true,
  reference_resolution_enabled: true,
  smart_context_analysis_enabled: true,
  historical_changes_enabled: true,
};

const rows: Array<{ key: keyof ContextIntelligenceSettings; label: string; description: string }> = [
  { key: "shared_context_enabled", label: "Shared Context", description: "Use prior chat context when answering." },
  { key: "recent_context_enabled", label: "Recent Conversation", description: "Include recent user and assistant messages." },
  { key: "structured_memory_enabled", label: "Structured Memory", description: "Remember durable facts, decisions, constraints and goals." },
  { key: "rolling_summary_enabled", label: "Rolling Summary", description: "Compress older conversation into a bounded summary." },
  { key: "reference_resolution_enabled", label: "Reference Resolution", description: "Resolve phrases such as “that”, “previous”, and “earlier”." },
  { key: "smart_context_analysis_enabled", label: "Smart Context Analysis", description: "Let the Router choose additional relevant context." },
  { key: "historical_changes_enabled", label: "Historical Changes", description: "Track superseded decisions and previous values." },
];

export function ContextIntelligenceSettings({ settings, loading, error, savingKey, resetting, onRefresh, onToggle, onReset }: Props) {
  const stored = settings ?? DEFAULTS;
  const effective = settings?.effective ?? stored;
  const sharedOff = !effective.shared_context_enabled;

  return (
    <section className="panel-section context-intelligence-panel" aria-labelledby="context-intelligence-heading">
      <div className="context-intelligence-heading">
        <div>
          <h3 id="context-intelligence-heading">Context Intelligence</h3>
          <p>Controls how this local assistant reuses conversation state.</p>
        </div>
        <button type="button" className="tool-button" onClick={onRefresh} disabled={loading} aria-label="Refresh context settings" title="Refresh context settings">
          <RefreshCw size={13} className={loading ? "spin" : ""} />
          <span>{loading ? "Loading" : "Refresh"}</span>
        </button>
      </div>

      {error && <div className="model-config-error" role="alert">{error} Context intelligence is using safe ON defaults until it is available.</div>}
      {sharedOff && <div className="context-settings-notice">Shared Context is off. Child preferences are retained but currently ineffective.</div>}

      <div className="context-toggle-list">
        {rows.map(({ key, label, description }) => {
          const isChild = key !== "shared_context_enabled";
          const isEffective = effective[key];
          return (
            <label className={`context-toggle-row${isChild && sharedOff ? " ineffective" : ""}`} key={key}>
              <span className="context-toggle-copy"><strong>{label}</strong><small>{description}</small></span>
              <span className="context-toggle-control">
                <input
                  type="checkbox"
                  role="switch"
                  aria-label={label}
                  checked={stored[key]}
                  disabled={loading || resetting || savingKey === key}
                  onChange={(event) => onToggle(key, event.target.checked)}
                />
                <span className="context-toggle-state">{isEffective ? "ON" : "OFF"}</span>
              </span>
            </label>
          );
        })}
      </div>

      <div className="context-settings-footer">
        <span>Stored in local SQLite</span>
        <button type="button" className="tool-button" onClick={onReset} disabled={loading || resetting}><RotateCcw size={13} />{resetting ? "Restoring…" : "Restore Context Defaults"}</button>
      </div>
    </section>
  );
}
