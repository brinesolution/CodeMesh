import type { NodeInspectorData } from "../graph/graphAdapter";

interface Props { inspector: NodeInspectorData | null; onClose: () => void; }

export function NodeInspector({ inspector, onClose }: Props) {
  if (!inspector) return <aside className="mesh-inspector mesh-inspector-empty"><span className="mesh-empty-kicker">Inspector</span><h3>Select a node</h3><p>Click a session, memory, message, package, or storage node to inspect its safe operational details.</p></aside>;
  return <aside className="mesh-inspector"><div className="mesh-inspector-head"><div><span>{inspector.type}</span><h3>Node details</h3></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close node details">×</button></div><h4>{inspector.title}</h4><dl>{inspector.fields.map((field) => <div key={field[0]}><dt>{field[0]}</dt><dd>{field[1]}</dd></div>)}</dl>{inspector.sourceMessageId && <button type="button" className="mesh-source-link">Show source · Message #{inspector.sourceMessageId}</button>}</aside>;
}
