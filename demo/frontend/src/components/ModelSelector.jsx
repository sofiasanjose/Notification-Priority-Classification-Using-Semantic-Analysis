import { MODEL_DISPLAY, MODEL_ORDER } from "../lib/urgency.js";

export default function ModelSelector({ value, onChange, available }) {
  const keys = (available && available.length ? available : MODEL_ORDER).filter(
    (k) => MODEL_DISPLAY[k]
  );
  return (
    <label className="flex items-center gap-2 text-xs text-slate-400">
      <span className="uppercase tracking-wider">Primary model</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100 outline-none transition hover:border-slate-500 focus:border-fuchsia-500"
      >
        {keys.map((k) => (
          <option key={k} value={k}>
            {MODEL_DISPLAY[k]}
          </option>
        ))}
      </select>
    </label>
  );
}
