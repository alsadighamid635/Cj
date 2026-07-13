"""
Chat API — the primary interface between the frontend and the RAG pipeline.

Endpoints:
  POST   /api/chat                             — send a message (± file), receive an AI reply
  GET    /api/chat/history/{session_id}        — fetch message history for a session
  GET    /api/chat/sessions                    — list all sessions for the requesting user
  DELETE /api/chat/session/{session_id}        — delete a session (owner only)
  PATCH  /api/chat/session/{session_id}/title  — rename a session

User identity:
  Each browser generates a persistent UUID stored in localStorage and sends it
  via the X-User-ID request header.  This provides conversation privacy without
  requiring a login system.  It is NOT a security boundary — it is a UX feature.

File uploads:
  The POST /api/chat endpoint accepts multipart/form-data so the user can
  optionally attach one image (JPEG/PNG/GIF/WebP) or document (PDF/TXT/DOCX).
  Images are forwarded to a Groq Vision model; document text is injected into
  the RAG context alongside retrieved knowledge-base chunks.
"""

import time
import uuid
from collections import defaultdict, deque
from typing import Annotated

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

import config
from core.file_processor import ALLOWED_TYPES, process_upload
from utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Injected at startup by main.py
_pipeline = None
_db = None


def init(pipeline, db) -> None:
    global _pipeline, _db
    _pipeline = pipeline
    _db = db


# ── Rate limiter ──────────────────────────────────────────────────────────────

class _SlidingWindowRateLimiter:
    """
    Simple in-memory sliding-window rate limiter.
    Allows up to `max_requests` calls per `window_seconds` per key.
    Thread-safe enough for a single-process server.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._buckets: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now    = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self._window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._max:
            return False
        bucket.append(now)
        return True


_rate_limiter = _SlidingWindowRateLimiter(
    max_requests=config.RATE_LIMIT_REQUESTS,
    window_seconds=config.RATE_LIMIT_WINDOW_SECONDS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_user_id(header_value: str | None) -> str:
    """
    Extract and sanitise the user ID from the X-User-ID header.
    Falls back to 'anonymous' if absent or malformed.
    """
    if not header_value:
        return "anonymous"
    uid = header_value.strip()[: config.MAX_USER_ID_LEN]
    return uid if uid else "anonymous"


def _make_title(text: str) -> str:
    """Derive a short display title from the first user message."""
    title = " ".join(text.split())
    if len(title) > config.MAX_SESSION_TITLE_LEN:
        title = title[: config.MAX_SESSION_TITLE_LEN - 3].rstrip() + "..."
    return title or "New Chat"


# ── Response model ────────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    reply:      str
    session_id: str
    confidence: str
    sources:    list[str]


class RenameTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=config.MAX_SESSION_TITLE_LEN)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    message:    str           = Form(...,  min_length=1, max_length=config.MAX_MESSAGE_LEN),
    session_id: str | None    = Form(None, max_length=64),
    file:       UploadFile | None = File(None),
    x_user_id:  Annotated[str | None, Header()] = None,
):
    """
    Main chat endpoint.  Accepts multipart/form-data with:
      • message    (required) — the user's text input
      • session_id (optional) — continue an existing conversation
      • file       (optional) — one image or document attachment
    """
    user_id = _resolve_user_id(x_user_id)

    # Rate limit per user
    if not _rate_limiter.is_allowed(user_id):
        logger.warning("Rate limit exceeded for user_id=%s", user_id[:16])
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment before sending another message.",
        )

    if not message.strip():
        raise HTTPException(status_code=422, detail="Message must not be blank.")

    # ── Optional file processing ───────────────────────────────────────────────
    processed_file = None
    if file and file.filename:
        ct = (file.content_type or "").lower().split(";")[0].strip()
        if ct not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=415,
                detail=(
                    "Unsupported file type. "
                    "Allowed: JPEG, PNG, GIF, WebP images · PDF, TXT, DOCX documents."
                ),
            )
        try:
            data = await file.read()
            processed_file = process_upload(file.filename, file.content_type or "", data)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        finally:
            await file.close()

    # ── Session wiring ─────────────────────────────────────────────────────────
    sid      = session_id or str(uuid.uuid4())
    is_first = _db.is_first_message(sid)
    _db.get_or_create_session(sid, user_id)

    # ── RAG + LLM ─────────────────────────────────────────────────────────────
    result = _pipeline.query(message, sid, attachment=processed_file)

    if is_first:
        title_text = message if not processed_file else f"[{processed_file.filename}] {message}"
        _db.rename_session(sid, _make_title(title_text))

    logger.debug(
        "chat session=%s user=%s confidence=%s has_file=%s",
        sid[:8], user_id[:8], result.confidence, processed_file is not None,
    )

    return ChatResponse(
        reply=result.text,
        session_id=sid,
        confidence=result.confidence,
        sources=result.sources,
    )


@router.get("/history/{session_id}")
async def history(session_id: str):
    return {"messages": _db.get_messages(session_id)}


@router.get("/sessions")
async def sessions(x_user_id: Annotated[str | None, Header()] = None):
    user_id = _resolve_user_id(x_user_id)
    return {"sessions": _db.list_sessions(user_id)}


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    x_user_id:  Annotated[str | None, Header()] = None,
):
    user_id = _resolve_user_id(x_user_id)
    deleted = _db.delete_session(session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found or access denied.")
    return {"ok": True}


@router.patch("/session/{session_id}/title")
async def rename_session(
    session_id: str,
    body:       RenameTitleRequest,
    x_user_id:  Annotated[str | None, Header()] = None,
):
    _resolve_user_id(x_user_id)
    _db.rename_session(session_id, body.title)
    return {"ok": True}
