import type { HeatmapFrame } from "@/types/config";
import type { StreamStatus } from "@/hooks/usePredictionStream";
import { HeatmapCanvas } from "./HeatmapCanvas";

interface MapPanelProps {
  running: boolean;
  status: StreamStatus;
  latest: HeatmapFrame | null;
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
  const cells = latest?.cells ?? null;
  const source = latest?.source ?? null;
  const updated = latest?.timestamp
    ? new Date(latest.timestamp).toLocaleTimeString()
    : "—";

  return (
    <section
      className="relative flex flex-col h-full rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-panelMuted overflow-hidden"
      aria-label="Dota 2 map"
    >
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-semibold tracking-wide">Live Heatmap</h2>
          <p className="text-xs text-slate-400">
            Coefficients from <code className="text-accent">heat_map</code> Redis key, overlaid on
            the Dota 2 minimap.
          </p>
        </div>
        <span className={pill.cls}>{pill.label}</span>
      </header>

      <div className="relative flex-1 flex items-center justify-center p-6">
        <div
          className="relative aspect-square w-full max-w-[720px] rounded-xl border border-slate-700/60 bg-slate-950 shadow-inner overflow-hidden"
          role="img"
          aria-label="Dota 2 map with prediction heatmap"
        >
          <img
            src="/dota-map.png"
            alt="Dota 2 minimap"
            className="absolute inset-0 h-full w-full select-none"
            draggable={false}
          />
          <HeatmapCanvas matrix={latest?.matrix ?? null} maxValue={latest?.max_value} />

          {!running && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
              <span className="px-4 py-2 rounded-full border border-slate-600 text-sm text-slate-300">
                Press Start to begin streaming
              </span>
            </div>
          )}
        </div>
      </div>

      <footer className="grid grid-cols-3 gap-4 px-6 py-4 border-t border-slate-800 bg-slate-950/40 text-xs">
        <div>
          <div className="uppercase tracking-widest text-slate-500">Grid</div>
          <div className="text-base font-semibold tabular-nums">
            {cells ? `${cells} × ${cells}` : "—"}
          </div>
        </div>
        <div>
          <div className="uppercase tracking-widest text-slate-500">Updated</div>
          <div className="text-base font-semibold tabular-nums">{updated}</div>
        </div>
        <div className="text-right">
          <div className="uppercase tracking-widest text-slate-500">Source</div>
          <div className="text-base font-semibold">
            {source === "redis" ? (
              <span className="text-radiant">redis</span>
            ) : source === "mock" ? (
              <span className="text-accent">mock</span>
            ) : (
              "—"
            )}
          </div>
        </div>
      </footer>
    </section>
  );
}
