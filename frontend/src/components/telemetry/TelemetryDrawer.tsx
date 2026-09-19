import { Activity, Cpu, HardDrive, MemoryStick, X } from "lucide-react";

import type { MetricsData, RouteData, SystemSnapshot } from "../../api/types";
import { formatBytes, formatPercent } from "../../lib/format";

interface Props { open: boolean; system: SystemSnapshot | null; route?: RouteData; metrics?: MetricsData; onClose: () => void; }

function Meter({ label, value, detail }: { label: string; value: number | null | undefined; detail: string }) {
  return <div className="metric-row"><span>{label}</span><div className="meter"><span style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }} /></div><span>{detail}</span></div>;
}

export function TelemetryDrawer({ open, system, route, metrics, onClose }: Props) {
  if (!open) return null;
  const ramPercent = system?.ram_used_bytes && system.ram_total_bytes ? (system.ram_used_bytes / system.ram_total_bytes) * 100 : null;
  const vramPercent = system?.vram_used_bytes && system.vram_total_bytes ? (system.vram_used_bytes / system.vram_total_bytes) * 100 : null;
  return <>
    <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
    <aside className="telemetry" role="dialog" aria-label="System telemetry">
      <div className="telemetry-head"><div><h2>Routing & telemetry</h2><p>Live local runtime signals. Polls while this panel is open.</p></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close telemetry"><X size={17} /></button></div>
      <section className="panel-section"><h3><Activity size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />Routing trace</h3>
        <div className="telemetry-card"><dl><dt>Route</dt><dd>{route?.expert ?? "—"}</dd><dt>Router</dt><dd>{route?.router_model ?? "Manual bypass"}</dd><dt>Confidence</dt><dd>{route ? `${Math.round(route.confidence * 100)}%` : "—"}</dd><dt>Route time</dt><dd>{route?.latency_ms == null ? "—" : `${Math.round(route.latency_ms)} ms`}</dd><dt>Generation</dt><dd>{metrics ? `${Math.round(metrics.generation_latency_ms)} ms` : "—"}</dd></dl></div>
      </section>
      <section className="panel-section"><h3>System telemetry</h3>
        <Meter label="CPU" value={system?.cpu_percent} detail={formatPercent(system?.cpu_percent)} />
        <Meter label="RAM" value={ramPercent} detail={system ? `${formatBytes(system.ram_used_bytes)} / ${formatBytes(system.ram_total_bytes)}` : "—"} />
        <Meter label="GPU" value={system?.gpu_utilization_percent} detail={formatPercent(system?.gpu_utilization_percent)} />
        <Meter label="VRAM" value={vramPercent} detail={system ? `${formatBytes(system.vram_used_bytes)} / ${formatBytes(system.vram_total_bytes)}` : "—"} />
      </section>
      <section className="panel-section"><h3>Runtime</h3><div className="telemetry-card"><dl><dt><Cpu size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />GPU</dt><dd>{system?.gpu_name ?? "Unavailable"}</dd><dt><MemoryStick size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />Active model</dt><dd>{system?.active_model ?? metrics?.model ?? "Idle"}</dd><dt><HardDrive size={12} style={{ verticalAlign: "-2px", marginRight: 4 }} />Ollama</dt><dd>{system?.ollama_reachable ? "Reachable" : "Unavailable"}</dd></dl></div></section>
    </aside>
  </>;
}

