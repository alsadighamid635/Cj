"""
Chat API endpoints.

POST /api/chat                      — send a message, get an AI response
GET  /api/chat/history/{session_id} — fetch message history for a session
GET  /api/chat/sessions             — list sessions for a user
DELETE /api/chat/session/{session_id} — delete a session and its messages
PATCH /api/chat/session/{session_id}/title — rename a session
"""

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])

_pipeline = None
_db = None


def init(pipeline, db):
    global _pipeline, _db
    _pipeline = pipeline
    _db = db


def _make_title(text: str) -> str:
    """Derive a short, clean title from the first user message."""
    # Strip leading/trailing whitespace and collapse internal whitespace
    title = " ".join(text.split())
    # Truncate to 45 chars with ellipsis if needed
    if len(title) > 45:
        title = title[:42].rstrip() + "..."
    return title or "New Chat"


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    confidence: str
    sources: list[str]


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Empty message")

    session_id = req.session_id or str(uuid.uuid4())
    user_id = req.user_id or "anonymous"

    # Auto-title: check BEFORE saving the message whether this is the first one
    is_first = _db.is_first_message(session_id)

    _db.get_or_create_session(session_id, user_id)
    result = _pipeline.query(req.message, session_id)

    # Set title from the first user message
    if is_first:
        title = _make_title(req.message)
        _db.rename_session(session_id, title)

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
async def sessions(user_id: str = "anonymous"):
    return {"sessions": _db.list_sessions(user_id)}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, user_id: str = "anonymous"):
    _db.delete_session(session_id, user_id)
    return {"ok": True}


@router.patch("/session/{session_id}/title")
async def rename_session(session_id: str, body: dict):
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(400, "Title cannot be empty")
    _db.rename_session(session_id, title[:45])
    return {"ok": True}
