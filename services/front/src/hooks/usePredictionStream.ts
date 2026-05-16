import { useEffect, useRef, useState } from "react";
import { predictionsUrl } from "@/lib/api";
import type { PredictionFrame } from "@/types/config";

export type StreamStatus = "idle" | "connecting" | "open" | "closed" | "error";

export interface PredictionStreamState {
  status: StreamStatus;
  latest: PredictionFrame | null;
}

export function usePredictionStream(token: string | null): PredictionStreamState {
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [latest, setLatest] = useState<PredictionFrame | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("idle");
      setLatest(null);
      return;
    }
    setStatus("connecting");
    const ws = new WebSocket(predictionsUrl(token));
    wsRef.current = ws;

    ws.onopen = () => setStatus("open");
    ws.onerror = () => setStatus("error");
    ws.onclose = () => setStatus((s) => (s === "error" ? "error" : "closed"));
    ws.onmessage = (ev) => {
      try {
        const frame = JSON.parse(ev.data) as PredictionFrame;
        setLatest(frame);
      } catch {
        // ignore malformed frames; the BFF mock guarantees valid JSON
      }
    };

    return () => {
      ws.close();
    };
  }, [token]);

  return { status, latest };
}
