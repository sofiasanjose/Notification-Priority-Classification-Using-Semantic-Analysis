"""
Gmail polling client.

First run opens a browser for OAuth consent and writes token.json.
Subsequent runs reuse the saved token.

Polls every `interval_s` seconds for unread messages, classifies each one
with every loaded model, pushes the result onto the shared asyncio.Queue,
then marks the message as read to avoid re-classifying.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

log = logging.getLogger("demo.gmail")

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
BACKEND_DIR = Path(__file__).parent
CREDENTIALS_FILE = BACKEND_DIR / "credentials.json"
TOKEN_FILE = BACKEND_DIR / "token.json"


def _authenticate() -> Credentials:
    """Run (or resume) the OAuth2 flow and return valid credentials."""
    creds: Optional[Credentials] = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Download OAuth client credentials "
                    "from Google Cloud Console (Desktop app type)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def _extract_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _extract_body(payload: dict) -> str:
    """Recursively find the first text/plain body, fall back to text/html."""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime.startswith("text/plain") and body.get("data"):
        try:
            return base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="replace")
        except Exception:
            pass

    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text

    if mime.startswith("text/html") and body.get("data"):
        try:
            html = base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="replace")
            import re
            return re.sub(r"<[^>]+>", " ", html)
        except Exception:
            pass
    return ""


def _fetch_unread(service, last_seen_epoch: int) -> list[dict]:
    """Return list of unread messages received after `last_seen_epoch` (seconds)."""
    query = f"is:unread after:{last_seen_epoch}"
    try:
        resp = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
    except HttpError as e:
        log.warning("Gmail list failed: %s", e)
        return []

    ids = [m["id"] for m in resp.get("messages", [])]
    messages: list[dict] = []
    for mid in ids:
        try:
            msg = service.users().messages().get(
                userId="me", id=mid, format="full"
            ).execute()
        except HttpError as e:
            log.warning("Gmail get(%s) failed: %s", mid, e)
            continue
        messages.append(msg)
    return messages


def _mark_read(service, message_id: str) -> None:
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except HttpError as e:
        log.warning("Mark-read failed for %s: %s", message_id, e)


async def poll_gmail_forever(hub, queue: asyncio.Queue, interval_s: int = 10) -> None:
    """Infinite polling loop — one iteration every `interval_s` seconds."""
    loop = asyncio.get_running_loop()

    # Auth runs once on startup (may block on the browser the first time).
    creds = await loop.run_in_executor(None, _authenticate)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # Only classify emails that arrive *after* the server starts, so restarting
    # the demo doesn't re-emit every unread email in the inbox.
    last_seen_epoch = int(time.time())
    log.info("Gmail poller starting — only messages newer than epoch=%d", last_seen_epoch)

    while True:
        try:
            messages = await loop.run_in_executor(
                None, _fetch_unread, service, last_seen_epoch
            )

            # Sort oldest first so the queue order matches arrival order.
            messages.sort(key=lambda m: int(m.get("internalDate", 0)))

            for msg in messages:
                payload = msg.get("payload", {})
                headers = payload.get("headers", [])

                sender = _extract_header(headers, "From")
                subject = _extract_header(headers, "Subject") or "(no subject)"
                body = _extract_body(payload)
                snippet = (body or msg.get("snippet", "")).strip()[:200]

                # Training data is short notification content — match that shape.
                text_for_model = f"{subject}. {snippet}".strip()

                try:
                    predictions = hub.classify_all(text_for_model)
                except Exception as e:
                    log.warning("Classification failed for %s: %s", msg.get("id"), e)
                    continue

                event = {
                    "id": msg["id"],
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "text": text_for_model,
                    "time_ms": int(msg.get("internalDate", 0)),
                    "predictions": predictions,
                }

                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop the oldest item if the queue is saturated.
                    _ = queue.get_nowait()
                    queue.put_nowait(event)

                # Advance the watermark past this message so we don't see it
                # again even if we fail to mark it read.
                ms = int(msg.get("internalDate", 0))
                if ms:
                    last_seen_epoch = max(last_seen_epoch, ms // 1000)

                await loop.run_in_executor(None, _mark_read, service, msg["id"])

        except Exception:
            log.exception("Unexpected error in Gmail poll loop")

        await asyncio.sleep(interval_s)
