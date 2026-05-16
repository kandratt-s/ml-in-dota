interface StartStopButtonProps {
  running: boolean;
  busy: boolean;
  onToggle: () => void;
}

export function StartStopButton({ running, busy, onToggle }: StartStopButtonProps) {
  const label = busy ? (running ? "Stopping…" : "Starting…") : running ? "Stop" : "Start";
  const baseClasses =
    "w-full py-4 rounded-xl font-semibold uppercase tracking-widest text-base transition shadow-lg";
  const palette = running
    ? "bg-dire hover:bg-dire/90 text-white shadow-dire/30"
    : "bg-radiant hover:bg-radiant/90 text-white shadow-radiant/30";
  return (
    <button
      type="button"
      className={`${baseClasses} ${palette} ${busy ? "opacity-70 cursor-wait" : ""}`}
      onClick={onToggle}
      disabled={busy}
      aria-pressed={running}
    >
      {label}
    </button>
  );
}
