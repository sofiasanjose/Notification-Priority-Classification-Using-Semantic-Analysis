"""
FastAPI application for the Notification Priority demo.

Endpoints
---------
POST /classify-all   Runs all loaded models on a single text.
GET  /stream         Server-Sent Events of classified Gmail messages.
GET  /model-stats    Static val/test metrics for the leaderboard.
GET  /health         Liveness probe.
"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from classifier import ROOT, get_hub

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("demo.main")


# ---------------------------------------------------------------------------
# Shared state — a single asyncio.Queue bridges the Gmail poller with SSE.
# ---------------------------------------------------------------------------
email_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=200)
# Broadcast fan-out: each connected SSE client gets its own queue, all fed
# from `email_queue`. This lets us support multiple tabs cleanly.
_subscribers: List[asyncio.Queue[dict]] = []
_subscribers_lock = asyncio.Lock()


async def _broadcast_loop() -> None:
    """Drain `email_queue` and copy each event to every subscriber."""
    while True:
        event = await email_queue.get()
        async with _subscribers_lock:
            dead: List[asyncio.Queue[dict]] = []
            for q in _subscribers:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(q)
            for q in dead:
                _subscribers.remove(q)


# ---------------------------------------------------------------------------
# Lifespan — load models on startup, kick off Gmail poller if configured.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Loading models...")
    hub = get_hub()
    log.info("Models ready: %s", hub.loaded_keys)

    broadcaster = asyncio.create_task(_broadcast_loop())

    gmail_task: Optional[asyncio.Task] = None
    creds_path = Path(__file__).parent / "credentials.json"
    if creds_path.exists():
        try:
            from gmail_client import poll_gmail_forever

            gmail_task = asyncio.create_task(
                poll_gmail_forever(hub, email_queue, interval_s=10)
            )
            log.info("Gmail poller started (interval=10s)")
        except Exception as e:
            log.warning("Gmail poller failed to start: %s", e)
    else:
        log.info(
            "No credentials.json found — skipping Gmail poller. "
            "Manual /classify-all still works."
        )

    try:
        yield
    finally:
        broadcaster.cancel()
        if gmail_task is not None:
            gmail_task.cancel()


app = FastAPI(title="Notification Priority Demo", lifespan=lifespan)

# CORS — Vite dev server defaults to localhost:5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    hub = get_hub()
    return {"status": "ok", "models": hub.loaded_keys}


@app.post("/classify-all")
async def classify_all(req: ClassifyRequest) -> dict:
    hub = get_hub()
    try:
        results = hub.classify_all(req.text)
    except Exception as e:
        log.exception("classify-all failed")
        raise HTTPException(status_code=500, detail=str(e))
    return {"text": req.text, "predictions": results}


@app.get("/model-stats")
async def model_stats() -> dict:
    """Read val/test metrics from the canonical result files."""
    stats: Dict[str, dict] = {}

    # RoBERTa
    roberta_path = ROOT / "results" / "roberta-base" / "val_metrics.json"
    if roberta_path.exists():
        data = json.loads(roberta_path.read_text())
        stats["roberta"] = {
            "display_name": "RoBERTa",
            "val_macro_f1": data.get("best_val_macro_f1"),
            "test_macro_f1": data.get("test_macro_f1"),
            "history": data.get("history", []),
        }

    # BERT
    bert_path = ROOT / "results" / "bert-base-uncased" / "val_metrics.json"
    if bert_path.exists():
        data = json.loads(bert_path.read_text())
        stats["bert"] = {
            "display_name": "BERT",
            "val_macro_f1": data.get("best_val_macro_f1"),
            "test_macro_f1": data.get("test_macro_f1"),
            "history": data.get("history", []),
        }

    # TF-IDF baseline
    base_path = ROOT / "results" / "baseline" / "val_metrics.json"
    if base_path.exists():
        data = json.loads(base_path.read_text())
        stats["tfidf"] = {
            "display_name": "TF-IDF + LR",
            "val_macro_f1": data.get("val_macro_f1"),
            "test_macro_f1": data.get("test_macro_f1"),
            "val_accuracy": data.get("val_accuracy"),
            "test_accuracy": data.get("test_accuracy"),
        }

    return stats


@app.get("/stream")
async def stream() -> StreamingResponse:
    """SSE endpoint — emits one event per classified email."""

    async def event_generator() -> AsyncGenerator[str, None]:
        q: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        async with _subscribers_lock:
            _subscribers.append(q)

        # Initial handshake event — lets the frontend detect connection.
        yield f"event: ready\ndata: {json.dumps({'ok': True})}\n\n"

        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive comment — prevents proxies from closing idle connections.
                    yield ": keep-alive\n\n"
        finally:
            async with _subscribers_lock:
                if q in _subscribers:
                    _subscribers.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
