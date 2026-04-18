import UrgencyBadge from "./UrgencyBadge.jsx";
import ConfidenceBar from "./ConfidenceBar.jsx";
import { MODEL_DISPLAY, MODEL_ORDER } from "../lib/urgency.js";

export default function ModelComparison({ predictions, activeModel }) {
  if (!predictions) return null;

  const keys = MODEL_ORDER.filter((k) => predictions[k]);
  const labels = keys.map((k) => predictions[k].label);
  const disagree = new Set(labels).size > 1;

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">
          Model comparison
        </h3>
        {disagree && (
          <span className="rounded-md bg-fuchsia-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-fuchsia-300">
            models disagree
          </span>
        )}
      </div>

      <div className="grid gap-2.5 sm:grid-cols-3">
        {keys.map((k) => {
          const p = predictions[k];
          const isActive = k === activeModel;
          return (
            <div
              key={k}
              className={`rounded-lg border p-3 transition ${
                isActive
                  ? "border-fuchsia-500/60 bg-fuchsia-500/5"
                  : "border-slate-800 bg-slate-950/40"
              } ${disagree ? "ring-1 ring-fuchsia-500/20" : ""}`}
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-300">
                  {p.display_name || MODEL_DISPLAY[k]}
                </span>
                {isActive && (
                  <span title="Active model" className="text-xs">
                    👑
                  </span>
                )}
              </div>
              <div className="mb-2">
                <UrgencyBadge label={p.label} size="sm" />
              </div>
              <ConfidenceBar scores={p.scores} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
