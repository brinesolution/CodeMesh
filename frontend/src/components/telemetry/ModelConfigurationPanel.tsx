import { RefreshCw, RotateCcw } from "lucide-react";

import type { ModelConfiguration, ModelRole } from "../../api/types";

interface Props {
  configuration: ModelConfiguration | null;
  error: string | null;
  loading: boolean;
  savingRole: ModelRole | null;
  resetting: boolean;
  onRefresh: () => void;
  onAssign: (role: ModelRole, model: string) => void;
  onReset: () => void;
}

const roles: Array<{ key: ModelRole; label: string }> = [
  { key: "router", label: "Router" },
  { key: "conversation", label: "Conversation" },
  { key: "stem", label: "Math & Science" },
  { key: "coding", label: "Coding" },
];

export function ModelConfigurationPanel({ configuration, error, loading, savingRole, resetting, onRefresh, onAssign, onReset }: Props) {
  return (
    <section className="panel-section model-config-panel" aria-labelledby="model-config-heading">
      <div className="model-config-heading">
        <div>
          <h3 id="model-config-heading">Model Configuration</h3>
          <p>Choose from the models currently installed in Ollama.</p>
        </div>
        <button type="button" className="tool-button model-refresh" onClick={onRefresh} disabled={loading} aria-label="Refresh models" title="Refresh models">
          <RefreshCw size={13} className={loading ? "spin" : ""} />
          <span>{loading ? "Scanning" : "Refresh"}</span>
        </button>
      </div>

      {error && <div className="model-config-error" role="alert">{error}</div>}
      {configuration && <div className={`model-runtime-status ${configuration.ollama_reachable ? "" : "offline"}`}><span className={`status-dot ${configuration.ollama_reachable ? "" : "offline"}`} />{configuration.ollama_reachable ? `${configuration.available_models.length} Ollama models available` : "Ollama unavailable"}</div>}

      {loading && !configuration && <div className="model-config-empty">Scanning the local Ollama catalog…</div>}
      {configuration && configuration.available_models.length === 0 && <div className="model-config-empty">No installed Ollama models were returned. Start Ollama and refresh.</div>}

      {configuration && roles.map(({ key, label }) => {
        const selected = configuration.assignments[key];
        const availableNames = configuration.available_models.map((model) => model.name);
        const options = selected && !availableNames.includes(selected) ? [selected, ...availableNames] : availableNames;
        return (
          <label className="model-role" key={key}>
            <span>{label}</span>
            <select aria-label={`${label} model`} value={selected ?? ""} disabled={loading || savingRole === key || options.length === 0} onChange={(event) => onAssign(key, event.target.value)}>
              {selected && !availableNames.includes(selected) && <option value={selected}>{selected} (not installed)</option>}
              {options.filter((model, index) => options.indexOf(model) === index).map((model) => <option value={model} key={model}>{model}</option>)}
            </select>
            {savingRole === key && <small>Applying…</small>}
          </label>
        );
      })}

      <div className="model-config-footer">
        <span>{configuration ? `${configuration.available_models.length} discovered model${configuration.available_models.length === 1 ? "" : "s"}` : "Model list not loaded"}</span>
        <button type="button" className="tool-button" onClick={onReset} disabled={!configuration || resetting || loading}><RotateCcw size={13} />{resetting ? "Restoring…" : "Restore defaults"}</button>
      </div>
    </section>
  );
}
