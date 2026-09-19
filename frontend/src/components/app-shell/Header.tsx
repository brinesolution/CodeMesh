import { Activity, Menu } from "lucide-react";

import type { Mode } from "../../api/types";
import { modeLabel } from "../../lib/format";

interface Props { mode: Mode; online: boolean | null; onMenu: () => void; onTelemetry: () => void; }

export function Header({ mode, online, onMenu, onTelemetry }: Props) {
  return (
    <header className="topbar">
      <button type="button" className="icon-button mobile-only" onClick={onMenu} aria-label="Open sidebar"><Menu size={18} /></button>
      <div className="topbar-title"><h1>{modeLabel(mode)} workspace</h1><p>Ask, build, analyze — all on your local machine.</p></div>
      <div className="connection"><span className={`status-dot ${online === false ? "offline" : ""}`} />{online === false ? "Offline" : "Connected"}</div>
      <button type="button" className="icon-button" onClick={onTelemetry} aria-label="Open system telemetry"><Activity size={18} /></button>
    </header>
  );
}

