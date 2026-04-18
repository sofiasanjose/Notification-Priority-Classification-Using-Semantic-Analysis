import { URGENCY_COLORS } from "../lib/urgency.js";

export default function UrgencyBadge({ label, size = "md" }) {
  const key = (label || "").toLowerCase();
  const c = URGENCY_COLORS[key] || URGENCY_COLORS.low;
  const sizeClass =
    size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-semibold uppercase tracking-wide ${c.badge} ${sizeClass}`}
    >
      {key || "—"}
    </span>
  );
}
