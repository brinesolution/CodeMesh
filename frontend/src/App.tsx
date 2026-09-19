import { useCallback, useEffect, useRef, useState } from "react";

import { api, streamChat } from "./api/client";
import type { ChatMessage, MetricsData, Mode, ModelConfiguration, ModelRole, RouteData, SessionContext, SessionDetail, SessionSummary, StreamEvent, SystemSnapshot, ValidationData } from "./api/types";
import { Sidebar } from "./components/app-shell/Sidebar";
import { Header } from "./components/app-shell/Header";
import { ChatView } from "./components/chat/ChatView";
import { TelemetryDrawer } from "./components/telemetry/TelemetryDrawer";
import { modeLabel } from "./lib/format";
import { latestAssistantMessage, metricsDataFromMessage, routeDataFromMessage, validationDataFromMessage } from "./lib/routing";

function errorMessage(code: string | undefined, fallback: string): string {
  return ({
    OLLAMA_UNAVAILABLE: "Local model service is not running. Start Ollama and retry.",
    MODEL_NOT_INSTALLED: "The selected local model is missing. Run scripts\\pull-models.ps1 and retry.",
    GENERATION_TIMEOUT: "The model took too long to respond. Retry or switch expert.",
    GENERATION_CANCELLED: "Generation stopped.",
    INPUT_TOO_LONG: "That message is longer than the local input limit.",
  } as Record<string, string>)[code ?? ""] ?? fallback;
}

export default function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<Mode>("auto");
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);
  const [system, setSystem] = useState<SystemSnapshot | null>(null);
  const [modelConfiguration, setModelConfiguration] = useState<ModelConfiguration | null>(null);
  const [modelError, setModelError] = useState<string | null>(null);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [savingModelRole, setSavingModelRole] = useState<ModelRole | null>(null);
  const [resettingModels, setResettingModels] = useState(false);
  const [sessionContext, setSessionContext] = useState<SessionContext | null>(null);
  const [contextError, setContextError] = useState<string | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [route, setRoute] = useState<RouteData | undefined>();
  const [validation, setValidation] = useState<ValidationData | undefined>();
  const [metrics, setMetrics] = useState<MetricsData | undefined>();
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const lastPromptRef = useRef<{ text: string; mode: Mode } | null>(null);

  const restoreSessionState = (detail: SessionDetail) => {
    const assistant = latestAssistantMessage(detail.messages);
    setMessages(detail.messages);
    setRoute(routeDataFromMessage(assistant, detail.preferred_mode, undefined, detail.id));
    setMetrics(metricsDataFromMessage(assistant));
    setValidation(validationDataFromMessage(assistant));
  };

  const refreshSessions = useCallback(async () => {
    try {
      const loaded = await api.listSessions();
      setSessions(loaded);
      setOnline(true);
      return loaded;
    } catch {
      setOnline(false);
      return [];
    }
  }, []);

  useEffect(() => {
    void refreshSessions().then(async (loaded) => {
      if (loaded[0]) {
        setActiveSessionId(loaded[0].id);
        setMode(loaded[0].preferred_mode ?? "auto");
        try { restoreSessionState(await api.getSession(loaded[0].id)); } catch { setOnline(false); }
      }
    });
  }, [refreshSessions]);

  useEffect(() => {
    if (!telemetryOpen) return;
    const poll = () => { void api.system().then((snapshot) => { setSystem(snapshot); setOnline(snapshot.ollama_reachable !== false); }).catch(() => setOnline(false)); };
    poll();
    const interval = window.setInterval(poll, 2000);
    return () => window.clearInterval(interval);
  }, [telemetryOpen]);

  const refreshModels = useCallback(async () => {
    setModelsLoading(true);
    setModelError(null);
    try {
      const configuration = await api.listModels();
      setModelConfiguration(configuration);
      return configuration;
    } catch (caught) {
      setModelError(caught instanceof Error ? caught.message : "The Ollama model list could not be loaded.");
      throw caught;
    } finally {
      setModelsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshModels().catch(() => undefined);
  }, [refreshModels]);

  useEffect(() => {
    const routerModel = modelConfiguration?.assignments.router;
    if (!routerModel) return;
    setRoute((current) => current && current.mode === "auto" && !current.router_model ? { ...current, router_model: routerModel } : current);
  }, [modelConfiguration]);

  const refreshContext = useCallback(async (requestedSessionId: string | null = activeSessionId) => {
    if (!requestedSessionId) {
      setSessionContext(null);
      setContextError(null);
      return null;
    }
    setContextLoading(true);
    setContextError(null);
    try {
      const context = await api.getSessionContext(requestedSessionId);
      if (requestedSessionId === activeSessionId) setSessionContext(context);
      return context;
    } catch (caught) {
      if (requestedSessionId === activeSessionId) setContextError(caught instanceof Error ? caught.message : "The shared context could not be loaded.");
      return null;
    } finally {
      setContextLoading(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    if (telemetryOpen) void refreshContext(activeSessionId);
  }, [activeSessionId, refreshContext, telemetryOpen]);

  const assignModel = useCallback(async (role: ModelRole, model: string) => {
    setSavingModelRole(role);
    setModelError(null);
    try {
      setModelConfiguration(await api.assignModel(role, model));
    } catch (caught) {
      setModelError(caught instanceof Error ? caught.message : "The model assignment could not be saved.");
    } finally {
      setSavingModelRole(null);
    }
  }, []);

  const resetModels = useCallback(async () => {
    setResettingModels(true);
    setModelError(null);
    try {
      setModelConfiguration(await api.resetModels());
    } catch (caught) {
      setModelError(caught instanceof Error ? caught.message : "The default model assignments could not be restored.");
    } finally {
      setResettingModels(false);
    }
  }, []);

  const selectSession = async (id: string) => {
    try {
      const detail = await api.getSession(id);
      setActiveSessionId(id); setMode(detail.preferred_mode ?? "auto"); setError(null); restoreSessionState(detail); setSidebarOpen(false);
    } catch { setError("That conversation could not be loaded."); }
  };

  const newChat = () => { abortRef.current?.abort(); setActiveSessionId(null); setSessionContext(null); setMessages([]); setInput(""); setMode("auto"); setError(null); setRoute(undefined); setValidation(undefined); setMetrics(undefined); setSidebarOpen(false); };

  const deleteSession = async (id: string) => {
    try { await api.deleteSession(id); const remaining = await refreshSessions(); if (id === activeSessionId) { if (remaining[0]) await selectSession(remaining[0].id); else newChat(); } } catch { setError("The conversation could not be deleted."); }
  };

  const handleEvent = (event: StreamEvent) => {
    if (event.type === "route") setRoute(event.data as unknown as RouteData);
    if (event.type === "token") {
      const text = String(event.data.text ?? "");
      setMessages((current) => { const next = [...current]; const last = next[next.length - 1]; if (last?.role === "assistant") next[next.length - 1] = { ...last, content: last.content + text }; return next; });
    }
    if (event.type === "validation") setValidation(event.data as unknown as ValidationData);
    if (event.type === "metrics") setMetrics(event.data as unknown as MetricsData);
    if (event.type === "error") { const data = event.data as { code?: string; message?: string }; setError(errorMessage(data.code, data.message ?? "The local request failed.")); setIsStreaming(false); }
    if (event.type === "done") setMessages((current) => current.map((message, index) => index === current.length - 1 ? { ...message, transient: false } : message));
  };

  const sendMessage = async (text = input, selectedMode = mode, displayUser = true) => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    setError(null); setInput(""); setRoute(undefined); setValidation(undefined); setMetrics(undefined); setIsStreaming(true);
    lastPromptRef.current = { text: trimmed, mode: selectedMode };
    let sessionId = activeSessionId;
    try {
      if (!sessionId) { const created = await api.createSession(selectedMode); sessionId = created.id; setActiveSessionId(sessionId); }
      if (displayUser) setMessages((current) => [...current, { id: `u-${Date.now()}`, role: "user", content: trimmed }, { id: `a-${Date.now()}`, role: "assistant", content: "", transient: true }]);
      else setMessages((current) => [...current.filter((message, index) => !(index === current.length - 1 && message.role === "assistant")), { id: `a-${Date.now()}`, role: "assistant", content: "", transient: true }]);
      const controller = new AbortController(); abortRef.current = controller;
      await streamChat({ message: trimmed, mode: selectedMode, sessionId }, controller.signal, handleEvent);
      await refreshSessions();
    } catch (caught) {
      if ((caught as Error).name !== "AbortError") setError(errorMessage(undefined, (caught as Error).message || "The local request failed."));
    } finally { setIsStreaming(false); abortRef.current = null; }
  };

  const stop = () => { abortRef.current?.abort(); setIsStreaming(false); setMessages((current) => current.map((message, index) => index === current.length - 1 && message.role === "assistant" ? { ...message, content: message.content || "Generation stopped.", transient: false } : message)); };
  const regenerate = () => { const prompt = lastPromptRef.current; if (prompt) void sendMessage(prompt.text, prompt.mode, false); };
  const promptCard = (prompt: string, promptMode: Mode) => { setMode(promptMode); void sendMessage(prompt, promptMode); };

  return <div className="app-shell">
    <Sidebar sessions={sessions} activeId={activeSessionId} open={sidebarOpen} ollamaOnline={online} onNew={newChat} onSelect={(id) => void selectSession(id)} onDelete={(id) => void deleteSession(id)} onClose={() => setSidebarOpen(false)} onTelemetry={() => setTelemetryOpen(true)} />
    {sidebarOpen && <button type="button" className="sidebar-backdrop" aria-label="Close sidebar" onClick={() => setSidebarOpen(false)} />}
    <div className="main-pane"><Header mode={mode} online={online} onMenu={() => setSidebarOpen(true)} onTelemetry={() => setTelemetryOpen(true)} /><ChatView sessionId={activeSessionId} routerModel={modelConfiguration?.assignments.router ?? null} messages={messages} input={input} mode={mode} isStreaming={isStreaming} error={error} route={route} validation={validation} metrics={metrics} onInput={setInput} onModeChange={setMode} onSend={() => void sendMessage()} onStop={stop} onPrompt={promptCard} onRegenerate={regenerate} /></div>
    <TelemetryDrawer open={telemetryOpen} system={system} route={route} metrics={metrics} modelConfiguration={modelConfiguration} modelError={modelError} modelsLoading={modelsLoading} savingModelRole={savingModelRole} resettingModels={resettingModels} onRefreshModels={() => void refreshModels()} onAssignModel={(role, model) => void assignModel(role, model)} onResetModels={() => void resetModels()} sessionId={activeSessionId} sessionContext={sessionContext} contextError={contextError} contextLoading={contextLoading} onRefreshContext={() => void refreshContext()} onClose={() => setTelemetryOpen(false)} />
  </div>;
}
