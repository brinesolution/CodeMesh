import { useCallback, useEffect, useRef, useState } from "react";

import { getContextMesh } from "../api/contextMeshApi";
import type { ContextMeshData } from "../api/types";

export function useContextMesh(sessionId: string | null, open: boolean, refreshKey = 0) {
  const [data, setData] = useState<ContextMeshData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    requestRef.current?.abort();
    if (!sessionId) {
      setData(null);
      setError(null);
      setLoading(false);
      return null;
    }
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const next = await getContextMesh(sessionId, controller.signal);
      setData(next);
      return next;
    } catch (caught) {
      if ((caught as Error).name === "AbortError") return null;
      setError(caught instanceof Error ? caught.message : "Context Mesh could not be loaded.");
      return null;
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
        setLoading(false);
      }
    }
  }, [sessionId]);

  useEffect(() => {
    if (!open) return;
    void refresh();
    return () => requestRef.current?.abort();
  }, [open, refresh, refreshKey]);

  return { data, loading, error, refresh };
}
