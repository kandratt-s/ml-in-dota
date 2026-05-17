interface OptionGroupProps<T extends string | number> {
  label: string;
  value: T;
  options: readonly T[];
  onChange: (v: T) => void;
  disabled?: boolean;
  format?: (v: T) => string;
}

export function OptionGroup<T extends string | number>({
  label,
  value,
  options,
  onChange,
  disabled,
  format,
}: OptionGroupProps<T>) {
  return (
    <fieldset className="space-y-2" aria-disabled={disabled}>
      <legend className="text-xs uppercase tracking-wider text-slate-400">{label}</legend>
      <div className="control-row" role="radiogroup" aria-label={label}>
        {options.map((opt) => {
          const active = opt === value;
          const text = format ? format(opt) : String(opt);
          return (
            <button
              key={String(opt)}
              type="button"
              role="radio"
              aria-checked={active}
              disabled={disabled}
              onClick={() => onChange(opt)}
              className={`control-chip ${active ? "control-chip-active" : ""} ${
                disabled ? "opacity-50 cursor-not-allowed" : ""
              }`}
            >
              {text}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
