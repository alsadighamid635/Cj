"""
Admin / stats API endpoints.

GET /api/admin/stats — combined DB and vector-store statistics (public, used by topbar)
GET /api/admin/users — list all registered users (admin only)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.auth import require_user
from core import vectorstore
import config

router = APIRouter(prefix="/api/admin", tags=["admin"])

_db = None


def init(db):
    global _db
    _db = db


def _require_admin(user_id: Annotated[str, Depends(require_user)]) -> str:
    """Allow only the designated admin account."""
    user = _db.get_user_by_id(user_id)
    if not user or user["username"].lower() != config.ADMIN_USERNAME.lower():
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user_id


@router.get("/stats")
async def stats():
    db_stats = _db.get_stats()
    return {
        **db_stats,
        "knowledge_vectors": vectorstore.count(config.COLLECTION_KNOWLEDGE),
        "source_vectors":    vectorstore.count(config.COLLECTION_SOURCES),
        "chat_vectors":      vectorstore.count(config.COLLECTION_CHAT),
        "total_vectors":     vectorstore.total_knowledge(),
    }


@router.get("/users")
async def list_users(_: Annotated[str, Depends(_require_admin)]):
    """Return all registered users. Admin only."""
    users = _db.list_all_users()
    return {"users": users, "total": len(users)}
