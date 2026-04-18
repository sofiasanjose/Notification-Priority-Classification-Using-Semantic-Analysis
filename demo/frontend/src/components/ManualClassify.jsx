import { useState } from "react";
import ModelComparison from "./ModelComparison.jsx";

const EXAMPLES = [
  "URGENT: Your account has been compromised. Verify your identity now!",
  "Dinner plans tonight at 8pm? Let me know.",
  "50% off everything this weekend — shop now",
  "Critical bug assigned to you: App crashes on login. Priority: P0.",
];

export default function ManualClassify({ activeModel }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function onClassify() {
    const t = text.trim();
    if (!t) return;
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/classify-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: t }),
      });
      if (!r.ok) throw new Error(`Server returned ${r.status}`);
      const data = await r.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Manual Test</h2>
        <p className="mt-0.5 text-sm text-slate-400">
          Type any notification text and run all 3 models against it.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          placeholder="Paste or type a notification..."
          className="w-full resize-none rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 outline-none transition focus:border-fuchsia-500"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onClassify();
          }}
        />

        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setText(ex)}
              className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-400 transition hover:border-slate-500 hover:text-slate-200"
            >
              {ex.length > 50 ? ex.slice(0, 50) + "…" : ex}
            </button>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Tip: press ⌘/Ctrl + Enter to classify
          </span>
          <button
            onClick={onClassify}
            disabled={loading || !text.trim()}
            className="rounded-md bg-fuchsia-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-fuchsia-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Classifying..." : "Classify"}
          </button>
        </div>

        {error && (
          <p className="mt-3 rounded-md border border-red-500/40 bg-red-500/10 p-2 text-xs text-red-300">
            {error}
          </p>
        )}
      </div>

      {result && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="mb-3 text-xs uppercase tracking-wider text-slate-500">
            Input
          </p>
          <p className="mb-4 text-sm text-slate-200">{result.text}</p>
          <ModelComparison
            predictions={result.predictions}
            activeModel={activeModel}
          />
        </div>
      )}
    </div>
  );
}
