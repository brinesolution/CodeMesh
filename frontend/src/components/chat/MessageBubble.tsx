import { Bot, Check, Clipboard, RefreshCw, User } from "lucide-react";
import { useState } from "react";

import type { ChatMessage, RouteData, ValidationData } from "../../api/types";
import { expertDisplayLabel, modelDisplayLabel } from "../../lib/format";
import { MarkdownRenderer } from "../markdown/MarkdownRenderer";
import { RoutingTrace } from "../routing/RoutingTrace";

interface Props {
  message: ChatMessage;
  route?: RouteData;
  validation?: ValidationData;
  modelSwitchLatency?: number | null;
  generationLatency?: number | null;
  onRegenerate?: () => void;
}

export function MessageBubble({ message, route, validation, modelSwitchLatency, generationLatency, onRegenerate }: Props) {
  const [copied, setCopied] = useState(false);
  const isAssistant = message.role === "assistant";
  const modelLabel = isAssistant ? modelDisplayLabel(message.model ?? route?.expert_model) : null;
  const expertLabel = isAssistant ? expertDisplayLabel(message.route) ?? route?.expert_name : null;
  const copy = async () => {
    await navigator.clipboard?.writeText(message.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };
  return (
    <article className={`message ${message.role}`}>
      <div className="message-avatar" aria-hidden="true">{isAssistant ? <Bot size={15} /> : <User size={15} />}</div>
      <div className="message-body">
        <div className="message-meta"><strong>{isAssistant ? "CodeMesh" : "You"}</strong>{isAssistant && (expertLabel || modelLabel) && <span className="message-model">{expertLabel}{expertLabel && modelLabel ? " · " : ""}{modelLabel}</span>}</div>
        <div className="message-text">{isAssistant ? <MarkdownRenderer content={message.content || "Thinking…"} /> : <p>{message.content}</p>}</div>
        {isAssistant && !message.transient && (
          <>
            <div className="message-actions">
              <button type="button" onClick={copy}>{copied ? <Check size={13} /> : <Clipboard size={13} />}{copied ? "Copied" : "Copy"}</button>
              {onRegenerate && <button type="button" onClick={onRegenerate}><RefreshCw size={13} />Regenerate</button>}
            </div>
            <RoutingTrace route={route} validation={validation} modelSwitchLatency={modelSwitchLatency} generationLatency={generationLatency} />
          </>
        )}
      </div>
    </article>
  );
}
