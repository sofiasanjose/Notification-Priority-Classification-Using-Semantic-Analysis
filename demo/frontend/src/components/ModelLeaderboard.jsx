import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import { MODEL_DISPLAY, MODEL_ORDER } from "../lib/urgency.js";

const MODEL_NOTES = {
  tfidf: "Lightweight baseline, no GPU needed",
  bert: "Fine-tuned bert-base-uncased (5 epochs)",
  roberta: "Fine-tuned roberta-base (5 epochs) — best val F1",
};

export default function ModelLeaderboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/model-stats")
      .then((r) => r.json())
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  if (error)
    return (
      <p className="text-sm text-red-400">Failed to load stats: {error}</p>
    );
  if (!stats)
    return <p className="text-sm text-slate-400">Loading...</p>;

  const rows = MODEL_ORDER.filter((k) => stats[k]).map((k) => ({
    key: k,
    name: stats[k].display_name || MODEL_DISPLAY[k],
    valF1: stats[k].val_macro_f1 ?? 0,
    testF1: stats[k].test_macro_f1 ?? 0,
    valAcc: stats[k].val_accuracy,
    testAcc: stats[k].test_accuracy,
    notes: MODEL_NOTES[k],
  }));

  const bestValIdx = rows
    .map((r, i) => [r.valF1, i])
    .sort((a, b) => b[0] - a[0])[0]?.[1];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Model Stats</h2>
        <p className="mt-0.5 text-sm text-slate-400">
          Validation and test macro-F1 across all trained models.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
        <h3 className="mb-4 text-sm font-semibold text-slate-200">
          Macro-F1 comparison
        </h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#1e293b" vertical={false} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis
                stroke="#94a3b8"
                fontSize={12}
                domain={[0, 1]}
                tickFormatter={(v) => v.toFixed(1)}
              />
              <Tooltip
                contentStyle={{
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(v) => v.toFixed(3)}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="valF1" name="Val macro-F1" fill="#a855f7">
                {rows.map((_, i) => (
                  <Cell key={i} fill={i === bestValIdx ? "#d946ef" : "#a855f7"} />
                ))}
              </Bar>
              <Bar dataKey="testF1" name="Test macro-F1" fill="#38bdf8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/70">
        <table className="w-full text-sm">
          <thead className="bg-slate-950/60 text-left text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Val F1</th>
              <th className="px-4 py-3">Test F1</th>
              <th className="px-4 py-3">Val Acc</th>
              <th className="px-4 py-3">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((r, i) => (
              <tr key={r.key} className={i === bestValIdx ? "bg-fuchsia-500/5" : ""}>
                <td className="px-4 py-3 font-medium text-slate-100">
                  {r.name}
                  {i === bestValIdx && (
                    <span className="ml-2 text-xs text-fuchsia-400">★ best</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {r.valF1 ? r.valF1.toFixed(3) : "—"}
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {r.testF1 ? r.testF1.toFixed(3) : "—"}
                </td>
                <td className="px-4 py-3 text-slate-400">
                  {r.valAcc ? r.valAcc.toFixed(3) : "—"}
                </td>
                <td className="px-4 py-3 text-slate-400">{r.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
