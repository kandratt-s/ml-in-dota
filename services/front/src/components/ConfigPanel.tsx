import {
  INTERVAL_OPTIONS,
  MODEL_OPTIONS,
  TIME_OPTIONS,
  type Interval,
  type ModelKind,
  type SessionConfig,
  type TimeWindow,
} from "@/types/config";
import { OptionGroup } from "./OptionGroup";
import { ToggleSwitch } from "./ToggleSwitch";

interface ConfigPanelProps {
  config: SessionConfig;
  onChange: (cfg: SessionConfig) => void;
  disabled: boolean;
}

export function ConfigPanel({ config, onChange, disabled }: ConfigPanelProps) {
  return (
    <section className="space-y-5" aria-label="Session configuration">
      <header>
        <h2 className="text-lg font-semibold tracking-wide">Configuration</h2>
        <p className="text-xs text-slate-400 mt-1">
          Settings are locked while a session is running.
        </p>
      </header>

      <OptionGroup<ModelKind>
        label="Model"
        value={config.model}
        options={MODEL_OPTIONS}
        onChange={(v) => onChange({ ...config, model: v })}
        disabled={disabled}
      />

      <OptionGroup<TimeWindow>
        label="Time window (sec)"
        value={config.time}
        options={TIME_OPTIONS}
        onChange={(v) => onChange({ ...config, time: v })}
        disabled={disabled}
      />

      <OptionGroup<Interval>
        label="Interval (sec)"
        value={config.interval}
        options={INTERVAL_OPTIONS}
        onChange={(v) => onChange({ ...config, interval: v })}
        disabled={disabled}
      />

      <ToggleSwitch
        label="Full map"
        checked={config.full_map}
        onChange={(v) => onChange({ ...config, full_map: v })}
        disabled={disabled}
      />
    </section>
  );
}
