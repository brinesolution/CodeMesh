import { useEffect, useState } from "react";
import { Activity, Cpu, HardDrive, MemoryStick, X } from "lucide-react";

import type { ContextIntelligenceSettings, ContextSettingsResponse, MetricsData, ModelConfiguration, ModelRole, RouteData, SessionContext, SystemSnapshot } from "../../api/types";
import { formatBytes, formatPercent, modeLabel } from "../../lib/format";
import { MemoryContextPanel } from "./MemoryContextPanel";
import { ModelConfigurationPanel } from "./ModelConfigurationPanel";
import { ContextIntelligenceSettings as ContextIntelligenceSettingsPanel } from "./ContextIntelligenceSettings";

interface Props {
  open: boolean;
  system: SystemSnapshot | null;
  route?: RouteData;
  metrics?: MetricsData;
  modelConfiguration: ModelConfiguration | null;
  modelError: string | null;
  modelsLoading: boolean;
  savingModelRole: ModelRole | null;
  resettingModels: boolean;
  onRefreshModels: () => void;
  onAssignModel: (role: ModelRole, model: string) => void;
  onResetModels: () => void;
  contextSettings: ContextSettingsResponse | null;
  contextSettingsError: string | null;
  contextSettingsLoading: boolean;
  savingContextKey: keyof ContextIntelligenceSettings | null;
  resettingContext: boolean;
  onRefreshContextSettings: () => void;
  onToggleContextSetting: (key: keyof ContextIntelligenceSettings, value: boolean) => void;
  onResetContextSettings: () => void;
  sessionId: string | null;
  sessionContext: SessionContext | null;
  contextError: string | null;
  contextLoading: boolean;
  onRefreshContext: () => void;
  onClose: () => void;
}

function Meter({ label, value, detail }: { label: string; value: number | null | undefined; detail: string }) {
  return <div className="metric-row"><span>{label}</span><div className="meter"><span style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }} /></div><span>{detail}</span></div>;
}

export function TelemetryDrawer({ open, system, route, metrics, modelConfiguration, modelError, modelsLoading, savingModelRole, resettingModels, onRefreshModels, onAssignModel, onResetModels, contextSettings, contextSettingsError, contextSettingsLoading, savingContextKey, resettingContext, onRefreshContextSettings, onToggleContextSetting, onResetContextSettings, sessionId, sessionContext, contextError, contextLoading, onRefreshContext, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<"overview" | "models" | "context">("overview");

  useEffect(() => {
    if (open) setActiveTab("overview");
  }, [open]);

  if (!open) return null;
  const ramPercent = system?.ram_used_bytes && system.ram_total_bytes ? (system.ram_used_bytes / system.ram_total_bytes) * 100 : null;
  const vramPercent = system?.vram_used_bytes && system.vram_total_bytes ? (system.vram_used_bytes / system.vram_total_bytes) * 100 : null;
  return <>
    <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
    <aside className="telemetry" role="dialog" aria-label="System telemetry">
      <div className="telemetry-head"><div><h2>Routing & telemetry</h2><p>Live local runtime signals. Polls while this panel is open.</p></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close telemetry"><X size={17} /></button></div>
      <nav className="telemetry-tabs" aria-label="System panel sections">
        <button type="button" className={activeTab === "overview" ? "active" : ""} aria-selected={activeTab === "overview"} onClick={() => setActiveTab("overview")}>Overview</button>
        <button type="button" className={activeTab === "models" ? "active" : ""} aria-selected={activeTab === "models"} onClick={() => { setActiveTab("models"); if (!modelConfiguration) onRefreshModels(); }}>Models</button>
        <button type="button" className={activeTab === "context" ? "active" : ""} aria-selected={activeTab === "context"} onClick={() => { setActiveTab("context"); onRefreshContext(); }}>Context</button>
      </nav>
      {activeTab === "models" ? <ModelConfigurationPanel configuration={modelConfiguration} error={modelError} loading={modelsLoading} savingRole={savingModelRole} resetting={resettingModels} onRefresh={onRefreshModels} onAssign={onAssignModel} onReset={onResetModels} /> : activeTab === "context" ? <><ContextIntelligenceSettingsPanel settings={contextSettings} loading={contextSettingsLoading} error={contextSettingsError} savingKey={savingContextKey} resetting={resettingContext} onRefresh={onRefreshContextSettings} onToggle={onToggleContextSetting} onReset={onResetContextSettings} /><MemoryContextPanel sessionId={sessionId} context={sessionContext} loading={contextLoading} error={contextError} onRefresh={onRefreshContext} /></> : <>
        <section className="panel-section"><h3><Activity size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />Routing trace</h3>
          <div className="telemetry-card"><dl><dt>Route</dt><dd>{route ? modeLabel(route.expert) : "Waiting for response"}</dd><dt>Router</dt><dd>{route ? route.router_model ?? "Manual selection" : "Select Auto or a specialist"}</dd><dt>Confidence</dt><dd>{route?.confidence == null ? "Not recorded" : `${Math.round(route.confidence * 100)}%`}</dd><dt>Route time</dt><dd>{route?.latency_ms == null ? "Not recorded" : `${Math.round(route.latency_ms)} ms`}</dd><dt>Context time</dt><dd>{route?.context_latency_ms == null ? "Not recorded" : `${Math.round(route.context_latency_ms)} ms`}</dd><dt>Generation</dt><dd>{metrics?.generation_latency_ms == null ? "Not recorded" : `${Math.round(metrics.generation_latency_ms)} ms`}</dd><dt>Expert model</dt><dd>{route?.expert_model_label ?? metrics?.model ?? "Not loaded"}</dd><dt>Context package</dt><dd>{metrics?.context ? `${metrics.context.recent_message_count} recent · ${metrics.context.memory_item_count} memory${metrics.context.summary_included ? " · summary" : ""}` : "Not recorded"}</dd><dt>Memory update</dt><dd>{metrics?.context?.memory_update_status ?? "Not recorded"}</dd><dt>Summary update</dt><dd>{metrics?.context?.summary_update_status ?? "Not recorded"}</dd><dt>Available routes</dt><dd>Auto · Conversation · Math &amp; Science · Coding</dd></dl></div>
        </section>
        <section className="panel-section"><h3>System telemetry</h3>
          <Meter label="CPU" value={system?.cpu_percent} detail={formatPercent(system?.cpu_percent)} />
          <Meter label="RAM" value={ramPercent} detail={system ? `${formatBytes(system.ram_used_bytes)} / ${formatBytes(system.ram_total_bytes)}` : "—"} />
          <Meter label="GPU" value={system?.gpu_utilization_percent} detail={formatPercent(system?.gpu_utilization_percent)} />
          <Meter label="VRAM" value={vramPercent} detail={system ? `${formatBytes(system.vram_used_bytes)} / ${formatBytes(system.vram_total_bytes)}` : "—"} />
        </section>
        <section className="panel-section"><h3>Runtime</h3><div className="telemetry-card"><dl><dt><Cpu size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />GPU</dt><dd>{system?.gpu_name ?? "Unavailable"}</dd><dt><MemoryStick size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />Active model</dt><dd>{system?.active_model ?? metrics?.model ?? "Idle"}</dd><dt><HardDrive size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />Ollama</dt><dd>{system?.ollama_reachable ? "Reachable" : "Unavailable"}</dd></dl></div></section>
      </>}
    </aside>
  </>;
}
