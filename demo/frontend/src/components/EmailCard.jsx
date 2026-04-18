import UrgencyBadge from "./UrgencyBadge.jsx";
import ConfidenceBar from "./ConfidenceBar.jsx";
import { formatTime, MODEL_DISPLAY } from "../lib/urgency.js";

export default function EmailCard({ email, activeModel, onClick }) {
  const pred = email.predictions?.[activeModel];
  if (!pred) return null;

  const allLabels = Object.values(email.predictions || {}).map((p) => p.label);
  const disagree = new Set(allLabels).size > 1;

  return (
    <button
      onClick={() => onClick?.(email)}
      className="group w-full animate-slide-in rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-left transition hover:border-slate-600 hover:bg-slate-900"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-medium text-slate-200">
              {email.sender || "Unknown sender"}
            </p>
            {disagree && (
              <span
                title="Models disagree on this email"
                className="rounded-md bg-fuchsia-500/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-fuchsia-300"
              >
                disagree
              </span>
            )}
          </div>
          <p className="mt-0.5 truncate text-sm font-semibold text-slate-100">
            {email.subject || "(no subject)"}
          </p>
          <p className="mt-1 line-clamp-2 text-xs text-slate-400">
            {email.snippet}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <UrgencyBadge label={pred.label} />
          <span className="text-[11px] text-slate-500">
            {formatTime(email.time_ms)}
          </span>
        </div>
      </div>

      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            {MODEL_DISPLAY[activeModel] || activeModel} confidence
          </span>
        </div>
        <ConfidenceBar scores={pred.scores} />
      </div>
    </button>
  );
}
