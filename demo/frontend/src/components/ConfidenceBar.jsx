import { URGENCY_COLORS } from "../lib/urgency.js";

const ORDER = ["high", "medium", "low"];

export default function ConfidenceBar({ scores, showLabels = true }) {
  if (!scores) return null;
  return (
    <div className="space-y-1.5">
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-800">
        {ORDER.map((lbl) => {
          const pct = (scores[lbl] || 0) * 100;
          if (pct <= 0) return null;
          return (
            <div
              key={lbl}
              className={URGENCY_COLORS[lbl].bar}
              style={{ width: `${pct}%` }}
              title={`${lbl}: ${pct.toFixed(1)}%`}
            />
          );
        })}
      </div>
      {showLabels && (
        <div className="flex justify-between text-[10px] text-slate-400">
          {ORDER.map((lbl) => (
            <span key={lbl} className={URGENCY_COLORS[lbl].text}>
              {lbl} {((scores[lbl] || 0) * 100).toFixed(0)}%
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
