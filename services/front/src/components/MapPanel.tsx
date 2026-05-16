import type { PredictionFrame } from "@/types/config";
import type { StreamStatus } from "@/hooks/usePredictionStream";

interface MapPanelProps {
  running: boolean;
  status: StreamStatus;
  latest: PredictionFrame | null;
}

function statusPill(status: StreamStatus, running: boolean) {
  if (!running) return { label: "Idle", cls: "pill pill-off" };
  switch (status) {
    case "open":
      return { label: "Live", cls: "pill pill-on animate-pulse" };
    case "connecting":
      return { label: "Connecting…", cls: "pill pill-off" };
    case "error":
      return { label: "Stream error", cls: "pill bg-dire/20 text-dire border-dire/40" };
    case "closed":
      return { label: "Disconnected", cls: "pill pill-off" };
    default:
      return { label: "Idle", cls: "pill pill-off" };
  }
}

export function MapPanel({ running, status, latest }: MapPanelProps) {
  const pill = statusPill(status, running);
  const prob = latest?.radiant_win_prob;
  const radiant = prob != null ? Math.round(prob * 100) : null;
  const dire = radiant != null ? 100 - radiant : null;

  return (
    <section
      className="relative flex flex-col h-full rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-panelMuted overflow-hidden"
      aria-label="Dota 2 map"
    >
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-semibold tracking-wide">Live Map</h2>
          <p className="text-xs text-slate-400">
            Predictions stream from the BFF over WebSocket.
          </p>
        </div>
        <span className={pill.cls}>{pill.label}</span>
      </header>

      <div className="relative flex-1 flex items-center justify-center p-6">
        <div
          className="relative aspect-square w-full max-w-[720px] rounded-xl border border-slate-700/60 bg-slate-950 shadow-inner overflow-hidden"
          role="img"
          aria-label="Dota 2 map placeholder"
        >
          <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
            <defs>
              <linearGradient id="riverGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1e3a5f" />
                <stop offset="100%" stopColor="#0f1f33" />
              </linearGradient>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path
                  d="M 10 0 L 0 0 0 10"
                  fill="none"
                  stroke="rgba(148,163,184,0.08)"
                  strokeWidth="0.5"
                />
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
            <polygon points="0,100 100,100 100,0" fill="rgba(58,125,58,0.18)" />
            <polygon points="0,100 0,0 100,0" fill="rgba(162,59,44,0.18)" />
            <path
              d="M 0 0 Q 50 50 100 100"
              stroke="url(#riverGrad)"
              strokeWidth="6"
              fill="none"
              opacity="0.6"
            />
            <circle cx="50" cy="50" r="4" fill="#e7b15a" opacity="0.7" />
          </svg>

          <div className="absolute top-3 left-3 text-xs font-semibold text-radiant uppercase tracking-widest">
            Radiant
          </div>
          <div className="absolute bottom-3 right-3 text-xs font-semibold text-dire uppercase tracking-widest">
            Dire
          </div>
        </div>
      </div>

      <footer className="grid grid-cols-2 gap-4 px-6 py-4 border-t border-slate-800 bg-slate-950/40">
        <div>
          <div className="text-xs uppercase tracking-widest text-radiant">Radiant win</div>
          <div className="text-3xl font-bold tabular-nums">
            {radiant != null ? `${radiant}%` : "—"}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase tracking-widest text-dire">Dire win</div>
          <div className="text-3xl font-bold tabular-nums">
            {dire != null ? `${dire}%` : "—"}
          </div>
        </div>
      </footer>
    </section>
  );
}
