import { useEffect, useMemo, useState } from "react";
import { Search, X } from "lucide-react";

import type { ContextMeshData, MeshView } from "./api/types";
import { ContextGraph } from "./graph/ContextGraph";
import { type GraphFilter, type NodeInspectorData } from "./graph/graphAdapter";
import { NodeInspector } from "./inspector/NodeInspector";
import { ContextPackageView } from "./context/ContextPackageView";
import { ContextTimeline } from "./timeline/ContextTimeline";
import { StorageExplorer } from "./storage/StorageExplorer";

interface Props {
  data: ContextMeshData | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onRetry?: () => void;
}

const initialFilters: Record<GraphFilter, boolean> = { messages: true, summary: true, memory: true, router: true, context: true, storage: true };

export function ContextMeshOverlay({ data, loading, error, onClose, onRetry }: Props) {
  const [view, setView] = useState<MeshView>("graph");
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState(initialFilters);
  const [showSuperseded, setShowSuperseded] = useState(true);
  const [inspector, setInspector] = useState<NodeInspectorData | null>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const memoryCount = useMemo(() => data ? data.memory.facts.length + data.memory.decisions.length + data.memory.constraints.length + data.memory.preferences.length + data.memory.open_tasks.length + (data.memory.current_goal ? 1 : 0) : 0, [data]);

  return <div className="context-mesh-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="context-mesh-overlay" role="dialog" aria-modal="true" aria-label="Context Mesh">
      <header className="context-mesh-header"><div className="context-mesh-title"><div className="context-mesh-mark">◉</div><div><span>SESSION INTELLIGENCE</span><h2>Context Mesh</h2><p>{data?.session.title ?? "New chat"} · {memoryCount} active memories · {data?.recent_context.count ?? 0} recent turns</p></div></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close Context Mesh"><X size={18} /></button></header>
      <nav className="context-mesh-tabs" aria-label="Context Mesh views" role="tablist">{(["graph", "context", "timeline", "storage"] as MeshView[]).map((tab) => <button type="button" role="tab" key={tab} aria-selected={view === tab} className={view === tab ? "active" : ""} onClick={() => { setView(tab); setInspector(null); }}>{tab[0].toUpperCase() + tab.slice(1)}</button>)}</nav>
      {view === "graph" && <div className="context-mesh-toolbar"><label className="mesh-search"><Search size={14} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search messages, memory, topics…" aria-label="Search Context Mesh" /></label><div className="mesh-filters">{(Object.keys(initialFilters) as GraphFilter[]).map((filter) => <label key={filter}><input type="checkbox" checked={filters[filter]} onChange={(event) => setFilters((current) => ({ ...current, [filter]: event.target.checked }))} />{filter}</label>)}<label><input type="checkbox" checked={showSuperseded} onChange={(event) => setShowSuperseded(event.target.checked)} />history</label></div></div>}
      {error ? <div className="mesh-contained-error" role="alert"><strong>Context Mesh unavailable</strong><p>{error}</p><button type="button" className="tool-button" onClick={onRetry}>Retry</button></div> : loading && !data ? <div className="mesh-loading"><span className="mesh-spinner" /><strong>Loading current session context…</strong></div> : !data ? <div className="mesh-empty-state"><span className="mesh-empty-kicker">No context yet</span><h3>This chat has no stored context.</h3><p>Session: empty · Raw history: 0 messages · Summary: not generated · Structured memory: empty · Recent context: 0 · Database: session will be created when you send the first message.</p></div> : view === "graph" ? <div className="context-mesh-body"><ContextGraph data={data} filters={filters} showSuperseded={showSuperseded} search={search} onSelect={setInspector} /><NodeInspector inspector={inspector} onClose={() => setInspector(null)} /></div> : <div className="context-mesh-scroll-body">{view === "context" && <ContextPackageView packageData={data.latest_context_package} />}{view === "timeline" && <ContextTimeline events={data.timeline} />}{view === "storage" && <StorageExplorer storage={data.storage} />}</div>}
    </section>
  </div>;
}
