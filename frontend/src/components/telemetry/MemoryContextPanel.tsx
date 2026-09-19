import { RefreshCw } from "lucide-react";

import type { MemoryItem, SessionContext } from "../../api/types";

interface Props {
  sessionId: string | null;
  context: SessionContext | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function ItemList({ label, items }: { label: string; items: MemoryItem[] }) {
  return (
    <section className="context-memory-group">
      <h4>{label}</h4>
      {items.length ? <ul>{items.map((item) => <li key={item.id}>{item.text}</li>)}</ul> : <p className="context-empty-line">None recorded</p>}
    </section>
  );
}

export function MemoryContextPanel({ sessionId, context, loading, error, onRefresh }: Props) {
  if (!sessionId) {
    return <section className="panel-section context-panel"><div className="context-empty">Select or start a chat to inspect its shared context.</div></section>;
  }

  const hasContext = Boolean(
    context?.summary || context?.current_topic || context?.memory.current_goal ||
    context?.memory.facts.length || context?.memory.decisions.length ||
    context?.memory.constraints.length || context?.memory.preferences.length ||
    context?.memory.open_tasks.length || context?.memory.topics.length,
  );

  return (
    <section className="panel-section context-panel" aria-labelledby="context-panel-heading">
      <div className="context-panel-heading">
        <div>
          <h3 id="context-panel-heading">Memory &amp; Context</h3>
          <p>Router-derived context for this conversation only.</p>
        </div>
        <button type="button" className="tool-button" onClick={onRefresh} disabled={loading} aria-label="Refresh context" title="Refresh context">
          <RefreshCw size={13} className={loading ? "spin" : ""} />
          <span>{loading ? "Refreshing" : "Refresh"}</span>
        </button>
      </div>
      {error && <div className="model-config-error" role="alert">{error}</div>}
      {loading && !context && <div className="context-empty">Loading shared context…</div>}
      {context && <>
        <div className="context-status-card">
          <div><span>Status</span><strong>{hasContext ? "Active" : "Empty"}</strong></div>
          <div><span>Topic</span><strong>{context.current_topic ?? "Not identified"}</strong></div>
          <div><span>Recent turns</span><strong>{context.recent_context_turns}</strong></div>
          <div><span>Router</span><strong>{context.router_model ?? "Not used yet"}</strong></div>
          <div><span>Memory model</span><strong>{context.last_memory_model ?? "Not used yet"}</strong></div>
          <div><span>Summary model</span><strong>{context.last_summary_model ?? "Not used yet"}</strong></div>
        </div>
        <section className="context-summary">
          <h4>Summary</h4>
          <p>{context.summary || "No rolling summary yet. It will appear as this chat becomes longer."}</p>
        </section>
        <section className="context-goal"><h4>Current goal</h4><p>{context.memory.current_goal ?? "No current goal recorded."}</p></section>
        <ItemList label="Facts" items={context.memory.facts} />
        <ItemList label="Decisions" items={context.memory.decisions} />
        <ItemList label="Constraints" items={context.memory.constraints} />
        <ItemList label="Preferences" items={context.memory.preferences} />
        <ItemList label="Open tasks" items={context.memory.open_tasks} />
        <section className="context-memory-group"><h4>Topics</h4><p>{context.memory.topics.length ? context.memory.topics.join(" · ") : "None recorded"}</p></section>
        <div className="context-meta">Summary through message {context.summary_through_message_id ?? "—"}{context.last_updated ? ` · Updated ${new Date(context.last_updated).toLocaleString()}` : ""}</div>
      </>}
    </section>
  );
}
