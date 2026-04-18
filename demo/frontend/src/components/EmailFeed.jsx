import { useEffect, useRef, useState } from "react";
import EmailCard from "./EmailCard.jsx";
import ModelSelector from "./ModelSelector.jsx";
import ModelComparison from "./ModelComparison.jsx";

export default function EmailFeed({ activeModel, setActiveModel, availableModels }) {
  const [emails, setEmails] = useState([]);
  const [connected, setConnected] = useState(false);
  const [selected, setSelected] = useState(null);
  const esRef = useRef(null);

  useEffect(() => {
    const es = new EventSource("/stream");
    esRef.current = es;

    es.addEventListener("ready", () => setConnected(true));
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setEmails((prev) => [data, ...prev].slice(0, 50));
      } catch (e) {
        console.warn("Bad SSE payload", e);
      }
    };

    return () => es.close();
  }, []);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_420px]">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">Live Inbox</h2>
            <p className="mt-0.5 text-sm text-slate-400">
              Polling Gmail every 10s · showing {emails.length} email
              {emails.length === 1 ? "" : "s"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={`flex items-center gap-1.5 text-xs ${
                connected ? "text-emerald-400" : "text-slate-500"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  connected ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
                }`}
              />
              {connected ? "Connected" : "Disconnected"}
            </span>
            <ModelSelector
              value={activeModel}
              onChange={setActiveModel}
              available={availableModels}
            />
          </div>
        </div>

        <div className="space-y-2.5">
          {emails.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-10 text-center">
              <p className="text-sm text-slate-400">
                Waiting for new unread emails...
              </p>
              <p className="mt-2 text-xs text-slate-600">
                Send yourself a test message to watch it appear here live.
              </p>
            </div>
          )}
          {emails.map((e) => (
            <EmailCard
              key={e.id}
              email={e}
              activeModel={activeModel}
              onClick={setSelected}
            />
          ))}
        </div>
      </div>

      <aside className="hidden lg:block">
        <div className="sticky top-6">
          {selected ? (
            <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  From
                </p>
                <p className="mt-0.5 truncate text-sm text-slate-200">
                  {selected.sender}
                </p>
                <p className="mt-2 text-xs uppercase tracking-wider text-slate-500">
                  Subject
                </p>
                <p className="mt-0.5 text-sm font-semibold text-slate-100">
                  {selected.subject}
                </p>
                <p className="mt-2 text-xs uppercase tracking-wider text-slate-500">
                  Snippet
                </p>
                <p className="mt-0.5 text-sm text-slate-400">
                  {selected.snippet}
                </p>
              </div>
              <ModelComparison
                predictions={selected.predictions}
                activeModel={activeModel}
              />
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-center">
              <p className="text-sm text-slate-400">
                Click an email to compare all 3 models
              </p>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
