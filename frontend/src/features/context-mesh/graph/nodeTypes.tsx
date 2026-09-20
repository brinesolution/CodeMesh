import { Handle, Position } from "@xyflow/react";

import type { MeshNodeData } from "./graphAdapter";

export function MeshNode({ data }: { data: MeshNodeData }) {
  return (
    <div
      className={`mesh-node ${data.active ? "active" : ""} ${data.searchMatch ? "search-match" : ""}`}
      style={{ "--node-accent": data.accent } as React.CSSProperties}
      role="button"
      tabIndex={0}
      aria-label={`${data.eyebrow}: ${data.title}`}
      title={data.preview}
    >
      <Handle type="target" position={Position.Left} />
      <div className="mesh-node-eyebrow"><span className="mesh-node-dot" />{data.eyebrow}</div>
      <div className="mesh-node-title">{data.title}</div>
      <div className="mesh-node-detail">{data.detail}</div>
      {data.status && <div className="mesh-node-status">{data.status}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export const meshNodeTypes = { mesh: MeshNode };
