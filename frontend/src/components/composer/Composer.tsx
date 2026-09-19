import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef } from "react";

import type { Mode } from "../../api/types";
import { modeLabel } from "../../lib/format";

interface Props {
  value: string;
  mode: Mode;
  isStreaming: boolean;
  onChange: (value: string) => void;
  onModeChange: (mode: Mode) => void;
  onSend: () => void;
  onStop: () => void;
}

export function Composer({ value, mode, isStreaming, onChange, onModeChange, onSend, onStop }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { ref.current?.focus(); }, []);
  const onKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); if (!isStreaming) onSend(); }
    if (event.key === "Escape" && isStreaming) { event.preventDefault(); onStop(); }
  };
  return (
    <div className="composer">
      <textarea ref={ref} value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={onKeyDown} placeholder="Ask CodeMesh anything…" aria-label="Message" />
      <div className="composer-footer">
        <select className="mode-select" value={mode} onChange={(event) => onModeChange(event.target.value as Mode)} aria-label="Routing mode">
          {(["auto", "conversation", "stem", "coding"] as Mode[]).map((item) => <option key={item} value={item}>{modeLabel(item)}</option>)}
        </select>
        <span className="composer-hint">Enter to send · Shift+Enter for newline</span>
        {isStreaming ? <button type="button" className="stop-button" onClick={onStop}><Square size={13} fill="currentColor" />Stop</button> : <button type="button" className="send-button" onClick={onSend} disabled={!value.trim()}><ArrowUp size={15} />Send</button>}
      </div>
    </div>
  );
}

