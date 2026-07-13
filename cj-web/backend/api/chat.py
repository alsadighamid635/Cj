"""
Chat API — the primary interface between the frontend and the RAG pipeline.

Endpoints:
  POST   /api/chat                         — send a message, receive an AI reply
  GET    /api/chat/history/{session_id}    — fetch message history for a session
  GET    /api/chat/sessions                — list all sessions for the requesting user
  DELETE /api/chat/session/{session_id}    — delete a session (owner only)
  PATCH  /api/chat/session/{session_id}/title — rename a session

User identity:
  Each browser generates a persistent UUID stored in localStorage and sends it
  via the X-User-ID request header.  This provides conversation privacy without
  requiring a login system.  It is NOT a security boundary — it is a UX feature.
"""

import time
import uuid
from collections import defaultdict, deque
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

import config
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
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self._window
        # Evict timestamps outside the current window
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
    uid = header_value.strip()[:config.MAX_USER_ID_LEN]
    return uid if uid else "anonymous"


def _make_title(text: str) -> str:
    """Derive a short display title from the first user message."""
    title = " ".join(text.split())
    if len(title) > config.MAX_SESSION_TITLE_LEN:
        title = title[: config.MAX_SESSION_TITLE_LEN - 3].rstrip() + "..."
    return title or "New Chat"


# ── Request / response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=config.MAX_MESSAGE_LEN)
    session_id: str | None = Field(default=None, max_length=64)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message must not be blank.")
        return v


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    confidence: str
    sources: list[str]


class RenameTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=config.MAX_SESSION_TITLE_LEN)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    x_user_id: Annotated[str | None, Header()] = None,
):
    user_id = _resolve_user_id(x_user_id)

    # Rate limit per user
    if not _rate_limiter.is_allowed(user_id):
        logger.warning("Rate limit exceeded for user_id=%s", user_id[:16])
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment before sending another message.",
        )

    session_id = req.session_id or str(uuid.uuid4())
    is_first = _db.is_first_message(session_id)

    _db.get_or_create_session(session_id, user_id)
    result = _pipeline.query(req.message, session_id)

    # Auto-title: only on the first message of a new session
    if is_first:
        _db.rename_session(session_id, _make_title(req.message))

    logger.debug(
        "chat session=%s user=%s confidence=%s",
        session_id[:8], user_id[:8], result.confidence,
    )

    return ChatResponse(
        reply=result.text,
        session_id=session_id,
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
    x_user_id: Annotated[str | None, Header()] = None,
):
    user_id = _resolve_user_id(x_user_id)
    deleted = _db.delete_session(session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found or access denied.")
    return {"ok": True}


@router.patch("/session/{session_id}/title")
async def rename_session(
    session_id: str,
    body: RenameTitleRequest,
    x_user_id: Annotated[str | None, Header()] = None,
):
    _resolve_user_id(x_user_id)   # validate header format
    _db.rename_session(session_id, body.title)
    return {"ok": True}
