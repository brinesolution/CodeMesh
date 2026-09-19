import { ChevronDown, GitBranch } from "lucide-react";
import { useState } from "react";

import type { RouteData, ValidationData } from "../../api/types";
import { modeLabel } from "../../lib/format";

interface Props { route?: RouteData; validation?: ValidationData; modelSwitchLatency?: number | null; generationLatency?: number | null; }

export function RoutingTrace({ route, validation, modelSwitchLatency, generationLatency }: Props) {
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
            <div className="route-detail">Confidence<strong>{route.confidence == null ? "Not recorded" : `${Math.round(route.confidence * 100)}%`}</strong></div>
            <div className="route-detail">Route time<strong>{route.latency_ms == null ? "—" : `${Math.round(route.latency_ms)} ms`}</strong></div>
            <div className="route-detail">Expert model<strong>{route.expert_model_label}</strong></div>
            <div className="route-detail">Model switch<strong>{modelSwitchLatency == null ? "—" : `${Math.round(modelSwitchLatency)} ms`}</strong></div>
            <div className="route-detail">Generation<strong>{generationLatency == null ? "Not recorded" : `${Math.round(generationLatency)} ms`}</strong></div>
            <div className="route-detail">Context<strong>{route.context_latency_ms == null ? "Not recorded" : `${Math.round(route.context_latency_ms)} ms${route.context_fallback ? " · fallback" : ""}`}</strong></div>
            <div className="route-detail">History<strong>{route.requires_history ? `${route.recent_turns_needed ?? 0} recent turns${route.requires_summary ? " + summary" : ""}` : "Not needed"}</strong></div>
          </div>
          <div className="route-detail">Topic<strong>{route.topic ?? "Not identified"}</strong></div>
          <div className="route-detail">Reason<strong>{route.reason}</strong></div>
          {validation && <div className="route-detail">Validation<strong>{validation.status === "valid" ? validation.detail : validation.status.replaceAll("_", " ")}</strong></div>}
        </div>
      )}
    </div>
  );
}
