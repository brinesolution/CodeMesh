import { useMemo, useState } from "react";
import { Background, Controls, MiniMap, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { ContextMeshData } from "../api/types";
import { buildContextGraph, type GraphFilter, type InspectorField, type NodeInspectorData } from "./graphAdapter";
import { meshNodeTypes } from "./nodeTypes";

interface Props {
  data: ContextMeshData;
  filters: Record<GraphFilter, boolean>;
  showSuperseded: boolean;
  search: string;
  onSelect: (inspector: NodeInspectorData) => void;
}

export function ContextGraph({ data, filters, showSuperseded, search, onSelect }: Props) {
  const [hovered, setHovered] = useState<NodeInspectorData | null>(null);
  const { nodes, edges } = useMemo(() => buildContextGraph(data, { filters, showSuperseded, search }), [data, filters, search, showSuperseded]);
  return (
    <div className="context-graph" aria-label="Context relationship graph">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={meshNodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2, minZoom: 0.35, maxZoom: 1.15 }}
        onNodeClick={(_, node) => onSelect(node.data.inspector)}
        onNodeMouseEnter={(_, node) => setHovered(node.data.inspector)}
        onNodeMouseLeave={() => setHovered(null)}
      >
        <Background color="#263749" gap={24} size={1} />
        <Controls showInteractive={false} position="bottom-left" />
        {nodes.length > 16 && <MiniMap nodeColor={(node) => String((node.data as { accent?: string }).accent ?? "#52657a")} pannable zoomable position="bottom-right" />}
      </ReactFlow>
      {hovered && <div className="mesh-hover-preview" role="status"><span>{hovered.type}</span><strong>{hovered.title}</strong><p>{hovered.fields.find((field: InspectorField) => field[0] === "Content")?.[1] ?? hovered.fields[0]?.[1] ?? "Select to inspect details."}</p></div>}
      {!nodes.length && <div className="mesh-graph-empty"><strong>No graph data matches these filters.</strong><span>Enable a category or clear search to continue.</span></div>}
    </div>
  );
}
