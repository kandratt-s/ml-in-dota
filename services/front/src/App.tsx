import { useCallback, useState } from "react";
import { ConfigPanel } from "@/components/ConfigPanel";
import { StartStopButton } from "@/components/StartStopButton";
import { GsiConfigBlock } from "@/components/GsiConfigBlock";
import { MapPanel } from "@/components/MapPanel";
import { startSession, stopSession } from "@/lib/api";
import { generateToken } from "@/lib/token";
import { usePredictionStream } from "@/hooks/usePredictionStream";
import { DEFAULT_CONFIG, type SessionConfig } from "@/types/config";

export default function App() {
  const [config, setConfig] = useState<SessionConfig>(DEFAULT_CONFIG);
  const [token, setToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const running = token !== null;
  const { status, latest } = usePredictionStream(token);

  const onToggle = useCallback(async () => {
    setErr(null);
    setBusy(true);
    try {
      if (running && token) {
        await stopSession(token);
        setToken(null);
      } else {
        const next = generateToken();
        await startSession({ token: next, config });
        setToken(next);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "unknown error");
    } finally {
      setBusy(false);
    }
  }, [running, token, config]);

  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-radiant to-dire" />
          <div>
            <h1 className="text-lg font-semibold tracking-wide">Dota 2 ML Tracker</h1>
            <p className="text-xs text-slate-400">Real-time win-probability predictions</p>
          </div>
        </div>
        <div className="text-xs text-slate-500">
          BFF: {(import.meta.env.VITE_BFF_BASE_URL as string | undefined) ?? "http://localhost:8080"}
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 p-6">
        <aside className="lg:col-span-1 space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-panelMuted/40 p-5 space-y-6">
            <ConfigPanel config={config} onChange={setConfig} disabled={running} />
            <StartStopButton running={running} busy={busy} onToggle={onToggle} />
            {err && (
              <div
                role="alert"
                className="text-xs text-dire bg-dire/10 border border-dire/30 rounded-md p-2"
              >
                {err}
              </div>
            )}
          </div>
          {token && <GsiConfigBlock token={token} />}
        </aside>

        <section className="lg:col-span-3">
          <MapPanel running={running} status={status} latest={latest} />
        </section>
      </div>
    </main>
  );
}
