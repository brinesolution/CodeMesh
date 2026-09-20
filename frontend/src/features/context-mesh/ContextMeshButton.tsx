import { Network } from "lucide-react";
import { useState } from "react";

interface Props {
  onClick: () => void;
  memoryCount?: number;
  recentCount?: number;
}

export function ContextMeshButton({ onClick, memoryCount, recentCount }: Props) {
  const [expanded, setExpanded] = useState(false);
  const isExpanded = expanded;
  return (
    <button
      type="button"
      className={`context-mesh-button ${isExpanded ? "expanded" : ""}`}
      aria-label="Open Context Mesh"
      onClick={onClick}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      onFocus={() => setExpanded(true)}
      onBlur={() => setExpanded(false)}
    >
      <Network size={15} aria-hidden="true" />
      <span className="context-mesh-label">{isExpanded ? "Context Mesh" : "Mesh"}</span>
      {isExpanded && <span className="context-mesh-counts">{memoryCount ?? "—"} memories · {recentCount ?? "—"} recent</span>}
    </button>
  );
}
