import { Activity, MessageSquare, Plus, Trash2, X } from "lucide-react";

import type { SessionSummary } from "../../api/types";
import { ContextMeshButton } from "../../features/context-mesh/ContextMeshButton";

interface Props {
  sessions: SessionSummary[];
  activeId: string | null;
  open: boolean;
  ollamaOnline: boolean | null;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
  onTelemetry: () => void;
  onContextMesh: () => void;
  meshMemoryCount?: number;
  meshRecentCount?: number;
}

export function Sidebar({ sessions, activeId, open, ollamaOnline, onNew, onSelect, onDelete, onClose, onTelemetry, onContextMesh, meshMemoryCount, meshRecentCount }: Props) {
  return (
    <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Conversations">
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-mark">CM</div>
          <span className="brand-name">CodeMesh</span>
          <span className="brand-note">LOCAL</span>
          <button type="button" className="icon-button mobile-only" onClick={onClose} aria-label="Close sidebar"><X size={17} /></button>
        </div>
        <button type="button" className="new-chat" onClick={onNew}><Plus size={17} />New chat</button>
      </div>

      <div className="sidebar-history">
        <div className="sidebar-label">Recent conversations</div>
        <div className="session-list">
          {sessions.length === 0 && <div className="status-detail" style={{ padding: "8px" }}>Your local chats will appear here.</div>}
          {sessions.map((session) => (
            <div key={session.id} className={`session-item ${session.id === activeId ? "active" : ""}`}>
              <button type="button" onClick={() => onSelect(session.id)} style={{ display: "flex", alignItems: "center", gap: 9, minWidth: 0, flex: 1, color: "inherit", background: "none", border: 0, textAlign: "left", padding: 0 }}>
                <MessageSquare size={15} /><span className="session-title">{session.title}</span>
              </button>
              <button type="button" className="icon-button" onClick={() => onDelete(session.id)} aria-label={`Delete ${session.title}`} style={{ width: 26, height: 26 }}><Trash2 size={13} /></button>
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-footer-controls">
          <div className="local-status">
            <div className="status-title"><span className={`status-dot ${ollamaOnline === false ? "offline" : ""}`} />{ollamaOnline === false ? "Ollama offline" : "Connected"}</div>
            <div className="status-detail">Local models stay on this machine.</div>
          </div>
          <button type="button" className="icon-button sidebar-telemetry" onClick={onTelemetry} aria-label="Open system telemetry"><Activity size={17} /></button>
        </div>
        <div className="sidebar-mesh-row"><ContextMeshButton onClick={onContextMesh} memoryCount={meshMemoryCount} recentCount={meshRecentCount} /></div>
      </div>
    </aside>
  );
}
