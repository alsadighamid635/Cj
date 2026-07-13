"""
Admin / stats API endpoints.

GET    /api/admin/stats         — combined DB and vector-store statistics (public)
GET    /api/admin/users         — list all registered users (admin only)
DELETE /api/admin/users/{uid}   — delete a user account (admin only)
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
    """Return all registered users with stats. Admin only."""
    users = _db.list_all_users()
    return {"users": users, "total": len(users)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_id: Annotated[str, Depends(_require_admin)],
):
    """Permanently delete a user account. Admin only. Cannot delete yourself."""
    if user_id == admin_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    deleted = _db.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True, "deleted_user_id": user_id}
