import type { MeshContextPackage } from "../api/types";

interface Props {
  packageData: MeshContextPackage | null;
}

export function ContextPackageView({ packageData }: Props) {
  if (!packageData) {
    return <section className="mesh-empty-view"><span className="mesh-empty-kicker">No context package</span><h3>The next specialist request will be recorded here.</h3><p>Context Mesh only reports packages that were actually assembled by CodeMesh. Nothing is inferred for older responses.</p></section>;
  }
  return <div className="mesh-context-view">
    <section className="mesh-context-hero"><span className="mesh-empty-kicker">Latest assembled context</span><h3>{packageData.expert_name}</h3><p>{packageData.model} · built {formatDate(packageData.created_at)}</p></section>
    <section className="mesh-context-section"><h4>SPECIALIST SYSTEM PROMPT</h4><pre>{packageData.system_prompt}</pre></section>
    <section className="mesh-context-section"><h4>PACKAGE INPUTS</h4><div className="mesh-context-stat-grid"><div><span>Summary</span><strong>{packageData.summary_included ? "Included" : "Not included"}</strong></div><div><span>Memory items</span><strong>{packageData.memory_items.length}</strong></div><div><span>Recent messages</span><strong>{packageData.recent_messages.length}</strong></div><div><span>Approx. size</span><strong>{packageData.approx_context_size} chars</strong></div></div></section>
    {packageData.summary_included && <section className="mesh-context-section"><h4>ROLLING SUMMARY</h4><p className="mesh-context-copy">{packageData.summary_text || "Summary was marked included, but no text is available."}</p><small>Through message #{packageData.summary_through_message_id ?? "—"}</small></section>}
    <section className="mesh-context-section"><h4>RELEVANT MEMORY</h4>{packageData.memory_items.length ? <div className="mesh-context-list">{packageData.memory_items.map((item) => <div className="mesh-context-item" key={item.id}><strong>{item.text}</strong><span>{item.source_message_id ? `Source message #${item.source_message_id}` : "Source not recorded"}</span></div>)}</div> : <p className="mesh-context-muted">No structured memory items were included.</p>}</section>
    {packageData.current_goal && <section className="mesh-context-section"><h4>CURRENT GOAL</h4><p className="mesh-context-copy">{packageData.current_goal}</p></section>}
    <section className="mesh-context-section"><h4>RECENT CONVERSATION</h4>{packageData.recent_messages.length ? <div className="mesh-context-list">{packageData.recent_messages.map((message) => <div className="mesh-context-item" key={message.id}><strong>{message.role === "user" ? "User" : "Assistant"} · Message #{message.id}</strong><span>{message.content}</span></div>)}</div> : <p className="mesh-context-muted">No recent messages were included.</p>}</section>
    <section className="mesh-context-section"><h4>CURRENT REQUEST</h4><p className="mesh-context-copy">{packageData.current_prompt || "Not available"}</p></section>
    <section className="mesh-context-section"><h4>OPERATIONAL METADATA</h4><div className="mesh-context-meta"><span>Router<strong>{packageData.router_model ?? "Not recorded"}</strong></span><span>Reference resolution<strong>{truthy(packageData.context_analysis.reference_detected)}</strong></span><span>History requested<strong>{truthy(packageData.context_analysis.requires_history)}</strong></span><span>Summary requested<strong>{truthy(packageData.context_analysis.requires_summary)}</strong></span></div></section>
  </div>;
}

function truthy(value: unknown): string { return value ? "Yes" : "No"; }
function formatDate(value: string): string { const date = new Date(value); return Number.isNaN(date.valueOf()) ? value : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); }
