import { useEffect, useState } from "react";
import EmailFeed from "./components/EmailFeed.jsx";
import ManualClassify from "./components/ManualClassify.jsx";
import ModelLeaderboard from "./components/ModelLeaderboard.jsx";

const TABS = [
  { id: "feed", label: "Live Feed" },
  { id: "manual", label: "Manual Test" },
  { id: "stats", label: "Model Stats" },
];

export default function App() {
  const [tab, setTab] = useState("feed");
  const [activeModel, setActiveModel] = useState("roberta");
  const [availableModels, setAvailableModels] = useState(["tfidf", "bert", "roberta"]);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data.models) && data.models.length) {
          setAvailableModels(data.models);
          if (!data.models.includes(activeModel)) {
            setActiveModel(data.models[data.models.length - 1]);
          }
        }
      })
      .catch(() => {})
      .finally(() => setBooting(false));
  }, []);

  return (
    <div className="mx-auto flex min-h-full max-w-6xl flex-col px-5 py-6">
      <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-50">
            Notification Priority
          </h1>
          <p className="mt-0.5 text-sm text-slate-400">
            Real-time urgency classification with TF-IDF, BERT, and RoBERTa
          </p>
        </div>
        <nav className="flex rounded-lg border border-slate-800 bg-slate-900/70 p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                tab === t.id
                  ? "bg-fuchsia-500 text-white"
                  : "text-slate-400 hover:text-slate-100"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex-1">
        {booting ? (
          <div className="flex h-64 items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-fuchsia-500" />
              Loading models...
            </div>
          </div>
        ) : tab === "feed" ? (
          <EmailFeed
            activeModel={activeModel}
            setActiveModel={setActiveModel}
            availableModels={availableModels}
          />
        ) : tab === "manual" ? (
          <ManualClassify activeModel={activeModel} />
        ) : (
          <ModelLeaderboard />
        )}
      </main>

      <footer className="mt-10 border-t border-slate-800 pt-4 text-center text-xs text-slate-500">
        NLP Project 10 · IE University · 2026
      </footer>
    </div>
  );
}
