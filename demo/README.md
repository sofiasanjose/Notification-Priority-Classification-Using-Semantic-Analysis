# Notification Priority Demo

Full-stack demo that polls Gmail, classifies every new email with **three** trained
models (TF-IDF + LR, BERT, RoBERTa), and streams results to a live React UI.

```
demo/
├── backend/     FastAPI + Gmail poller + 3 loaded models
└── frontend/    Vite + React + Tailwind + Recharts
```

---

## 1. Backend

### Install

```bash
cd demo/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The backend expects these artefacts to already exist in the project root
(produced by training):

```
models/tfidf_vectorizer.pkl
models/baseline_lr.pkl
results/bert-base-uncased/best_model/
results/roberta-base/best_model/
```

If any are missing, the backend will log a warning and simply skip that model.

### Run (without Gmail)

```bash
uvicorn main:app --reload --port 8000
```

All three models load once on startup. The `/stream` endpoint will stay open
but won't emit anything until Gmail is wired in.

### Test the model server in isolation

```bash
curl -X POST http://localhost:8000/classify-all \
  -H 'Content-Type: application/json' \
  -d '{"text": "URGENT: Your account has been compromised. Verify now!"}'

curl http://localhost:8000/model-stats
curl http://localhost:8000/health
```

### Enable Gmail polling (one-time setup)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create
   a new project → enable the **Gmail API**.
2. Configure the OAuth consent screen, add your Gmail as a **test user**.
3. Create **OAuth 2.0 credentials** of type **Desktop app**.
4. Download the JSON and save it as `demo/backend/credentials.json`.
5. Restart `uvicorn` — a browser window will open for consent the first time,
   producing `demo/backend/token.json`.

From then on, the poller queries unread mail every 10s, classifies each message
with all three models, pushes the result onto the SSE stream, and marks the
message as read.

Both `credentials.json` and `token.json` are in `.gitignore`.

---

## 2. Frontend

### Install & run

```bash
cd demo/frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

Vite proxies `/classify-all`, `/stream`, `/model-stats`, and `/health` to
`localhost:8000` — no CORS headaches.

### Tabs

- **Live Feed** — Gmail poller results via SSE. Each card shows the primary
  model's label + confidence bar; click to see all three models side-by-side.
  The header has a **primary model dropdown** — all three are always computed,
  only the feed badge changes.
- **Manual Test** — paste any text, run all three models, see disagreements.
- **Model Stats** — macro-F1 bar chart + leaderboard table built from
  `results/*/val_metrics.json`.

---

## 3. End-to-end

Two terminals:

```bash
# terminal 1
cd demo/backend && uvicorn main:app --reload --port 8000

# terminal 2
cd demo/frontend && npm run dev
```

Then send yourself a test email and watch it appear in the Live Feed with the
predicted urgency badge.
