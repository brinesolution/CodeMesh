import { Braces, FlaskConical, MessageCircle, Sparkles } from "lucide-react";

import type { ChatMessage, MetricsData, Mode, RouteData, ValidationData } from "../../api/types";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "../composer/Composer";

interface Props {
  messages: ChatMessage[];
  input: string;
  mode: Mode;
  isStreaming: boolean;
  error: string | null;
  route?: RouteData;
  validation?: ValidationData;
  metrics?: MetricsData;
  onInput: (value: string) => void;
  onModeChange: (mode: Mode) => void;
  onSend: () => void;
  onStop: () => void;
  onPrompt: (prompt: string, mode: Mode) => void;
  onRegenerate: () => void;
}

const prompts: Array<{ mode: Mode; title: string; description: string; prompt: string; icon: typeof MessageCircle }> = [
  { mode: "conversation", title: "Conversation", description: "Explain, summarize, and explore ideas.", prompt: "Explain cloud computing to a first-year engineering student.", icon: MessageCircle },
  { mode: "stem", title: "Math & Science", description: "Work through quantitative questions clearly.", prompt: "A 5 kg body experiences a force of 20 N. Find its acceleration.", icon: FlaskConical },
  { mode: "coding", title: "Coding", description: "Write, debug, and reason about software.", prompt: "Write merge sort in Java.", icon: Braces },
];

export function ChatView({ messages, input, mode, isStreaming, error, route, validation, metrics, onInput, onModeChange, onSend, onStop, onPrompt, onRegenerate }: Props) {
  const showEmpty = messages.length === 0;
  return <>
    <div className="chat-scroll"><main className="chat-content">
      {error && <div className="alert" role="alert">{error}</div>}
      {showEmpty ? <section className="empty-state"><div className="empty-kicker"><Sparkles size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />Local-first intelligence</div><h2>One workspace for <span>deeper work.</span></h2><p>CodeMesh routes each question to a focused local expert — keeping your work private while using the right model for the task.</p><div className="prompt-grid">{prompts.map(({ mode: promptMode, title, description, prompt, icon: Icon }) => <button type="button" key={promptMode} className="prompt-card" onClick={() => onPrompt(prompt, promptMode)}><span className="prompt-icon"><Icon size={16} /></span><h3>{title}</h3><p>{description}</p><span className="prompt-example">“{prompt}”</span></button>)}</div></section> : <div className="message-list">{messages.map((message, index) => <MessageBubble key={message.id} message={message} route={message.role === "assistant" ? route : undefined} validation={message.role === "assistant" ? validation : undefined} modelSwitchLatency={message.role === "assistant" ? metrics?.model_switch_latency_ms : undefined} generationLatency={message.role === "assistant" ? metrics?.generation_latency_ms : undefined} onRegenerate={!isStreaming && message.role === "assistant" && index === messages.length - 1 ? onRegenerate : undefined} />)}</div>}
    </main></div>
    <div className="composer-wrap"><div className="chat-content" style={{ paddingTop: 0, paddingBottom: 0 }}><Composer value={input} mode={mode} isStreaming={isStreaming} onChange={onInput} onModeChange={onModeChange} onSend={onSend} onStop={onStop} /></div></div>
  </>;
}
