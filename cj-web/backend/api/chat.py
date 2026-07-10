import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Set at startup by main.py
_pipeline = None
_db = None


def init(pipeline, db):
    global _pipeline, _db
    _pipeline = pipeline
    _db = db


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


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
    _db.get_or_create_session(session_id)
    result = _pipeline.query(req.message, session_id)
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
async def sessions():
    return {"sessions": _db.list_sessions()}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    _db.delete_session(session_id)
    return {"ok": True}
