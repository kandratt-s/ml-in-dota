import { useEffect, useRef, useState } from "react";
import { predictionsUrl } from "@/lib/api";
import type { HeatmapFrame } from "@/types/config";

export type StreamStatus = "idle" | "connecting" | "open" | "closed" | "error";

export interface PredictionStreamState {
  status: StreamStatus;
  latest: HeatmapFrame | null;
}

export function usePredictionStream(token: string | null): PredictionStreamState {
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [latest, setLatest] = useState<HeatmapFrame | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const connIdRef = useRef(0);

  // clear any pending reconnect when token becomes falsy
  useEffect(() => {
    if (!token && reconnectRef.current) {
      window.clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      setStatus("idle");
      setLatest(null);
      return;
    }
    let shouldStop = false;
    let backoff = 500; // ms
    const maxBackoff = 10000; // ms
    const myConnId = ++connIdRef.current;

    const connect = () => {
      if (shouldStop || !token) return;
      setStatus("connecting");
      const ws = new WebSocket(predictionsUrl(token));
      wsRef.current = ws;
      let opened = false;

      ws.onopen = () => {
        // ignore stale sockets
        if (myConnId !== connIdRef.current) return ws.close();
        opened = true;
        backoff = 500; // reset backoff on success
        setStatus("open");
      };

      ws.onerror = () => {
        if (myConnId !== connIdRef.current) return;
        setStatus("error");
      };

      ws.onclose = () => {
        if (myConnId !== connIdRef.current) return;
        // If connection never opened, treat as transient and attempt reconnect.
        if (!opened) {
          setStatus("connecting");
        } else {
          setStatus((s) => (s === "error" ? "error" : "closed"));
        }
        // schedule reconnect while token remains
        if (!shouldStop && token) {
          const wait = Math.min(backoff, maxBackoff);
          reconnectRef.current = window.setTimeout(() => {
            backoff = Math.min(maxBackoff, Math.floor(backoff * 1.5));
            connect();
          }, wait);
        }
      };

      ws.onmessage = (ev) => {
        if (myConnId !== connIdRef.current) return;
        try {
          const frame = JSON.parse(ev.data) as HeatmapFrame & { type?: string };
          // ignore heartbeat frames
          if (frame && (frame as any).type === "heartbeat") return;
          if (Array.isArray(frame.matrix)) setLatest(frame);
        } catch {
          // ignore malformed frames; the BFF guarantees valid JSON
        }
      };
    };

    // start initial connection
    connect();

    return () => {
      shouldStop = true;
      connIdRef.current += 1; // invalidate in-flight sockets
      if (reconnectRef.current) {
        window.clearTimeout(reconnectRef.current);
        reconnectRef.current = null;
      }
      try {
        wsRef.current?.close();
      } catch {
        // ignore
      }
    };
  }, [token]);

  return { status, latest };
}
