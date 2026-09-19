import { ChevronDown, GitBranch } from "lucide-react";
import { useState } from "react";

import type { RouteData, ValidationData } from "../../api/types";
import { modeLabel } from "../../lib/format";

interface Props { route?: RouteData; validation?: ValidationData; generationLatency?: number | null; }

export function RoutingTrace({ route, validation, generationLatency }: Props) {
  const [expanded, setExpanded] = useState(false);
  if (!route) return null;
  return (
    <div className="route-trace">
      <button type="button" className="route-summary" onClick={() => setExpanded((current) => !current)} aria-expanded={expanded}>
        <GitBranch size={13} color="var(--accent)" />
        <span>{modeLabel(route.mode)}</span>
        <strong>{route.expert_name}</strong>
        <span>· {route.expert_model_label}</span>
        <ChevronDown size={13} style={{ marginLeft: "auto", transform: expanded ? "rotate(180deg)" : undefined }} />
      </button>
      {expanded && (
        <div className="route-details">
          <div className="route-grid">
            <div className="route-detail">Router<strong>{route.router_model ?? "Bypassed · manual"}</strong></div>
            <div className="route-detail">Route<strong>{route.expert}</strong></div>
            <div className="route-detail">Confidence<strong>{Math.round(route.confidence * 100)}%</strong></div>
            <div className="route-detail">Route time<strong>{route.latency_ms == null ? "—" : `${Math.round(route.latency_ms)} ms`}</strong></div>
            <div className="route-detail">Expert model<strong>{route.expert_model_label}</strong></div>
            <div className="route-detail">Generation<strong>{generationLatency == null ? "—" : `${Math.round(generationLatency)} ms`}</strong></div>
          </div>
          <div className="route-detail">Reason<strong>{route.reason}</strong></div>
          {validation && <div className="route-detail">Validation<strong>{validation.status === "valid" ? validation.detail : validation.status.replaceAll("_", " ")}</strong></div>}
        </div>
      )}
    </div>
  );
}

