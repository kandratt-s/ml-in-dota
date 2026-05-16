import { useState } from "react";
import { buildGsiConfig } from "@/lib/gsi";

interface GsiConfigBlockProps {
  token: string;
}

export function GsiConfigBlock({ token }: GsiConfigBlockProps) {
  const text = buildGsiConfig(token);
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard might be unavailable (http context / older browsers); silent.
    }
  };

  return (
    <section
      className="rounded-xl border border-slate-700 bg-panelMuted/60 overflow-hidden"
      aria-label="GSI configuration"
    >
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <div>
          <h3 className="text-sm font-semibold">dota2-gsi Configuration</h3>
          <p className="text-xs text-slate-400">
            Save this to <code>cfg/gamestate_integration_ml.cfg</code>
          </p>
        </div>
        <button
          type="button"
          onClick={onCopy}
          className="text-xs px-3 py-1.5 rounded-md border border-slate-600 hover:border-accent hover:text-accent transition"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </header>
      <pre className="px-4 py-3 text-xs font-mono leading-relaxed text-slate-200 whitespace-pre overflow-x-auto">
        {text}
      </pre>
    </section>
  );
}
