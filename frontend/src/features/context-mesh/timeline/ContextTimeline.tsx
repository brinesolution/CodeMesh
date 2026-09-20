import type { MeshTimelineEvent } from "../api/types";

interface Props { events: MeshTimelineEvent[]; }

export function ContextTimeline({ events }: Props) {
  return <section className="mesh-timeline-view"><div className="mesh-view-heading"><div><span className="mesh-empty-kicker">Operational history</span><h3>Context timeline</h3><p>Durable messages, memory changes, routes, and context builds for this chat.</p></div><span className="mesh-count-pill">{events.length} events</span></div>{events.length ? <div className="mesh-timeline">{events.map((event) => <article className="mesh-timeline-event" key={event.id}><div className="mesh-timeline-marker" /><div className="mesh-timeline-copy"><div className="mesh-timeline-meta"><span>{event.type.replaceAll("_", " ")}</span><time>{formatDate(event.created_at)}</time></div><h4>{event.title}</h4><p>{event.detail}</p>{event.message_id && <small>Message #{event.message_id}</small>}</div></article>)}</div> : <div className="mesh-empty-inline">No timeline events yet. Start chatting to build the session history.</div>}</section>;
}

function formatDate(value: string): string { const date = new Date(value); return Number.isNaN(date.valueOf()) ? value : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); }
