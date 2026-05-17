import type { SessionConfig } from "@/types/config";

const BFF_BASE =
  (import.meta.env.VITE_BFF_BASE_URL as string | undefined) ?? "";

const WS_BASE =
  (import.meta.env.VITE_BFF_WS_URL as string | undefined) ??
  BFF_BASE.replace(/^http/, "ws");

export interface StartRequest {
  token: string;
  config: SessionConfig;
}

export async function startSession(req: StartRequest): Promise<void> {
  const res = await fetch(`${BFF_BASE}/api/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`start failed: ${res.status} ${body}`);
  }
}

export async function stopSession(token: string): Promise<void> {
  const res = await fetch(`${BFF_BASE}/api/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`stop failed: ${res.status} ${body}`);
  }
}

export function predictionsUrl(token: string): string {
  return `${WS_BASE}/ws/predictions?token=${encodeURIComponent(token)}`;
}
