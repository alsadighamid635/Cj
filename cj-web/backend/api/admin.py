"""
Admin / stats API endpoints.

GET /api/admin/stats — combined DB and vector-store statistics
"""

from fastapi import APIRouter
from core import vectorstore
import config

router = APIRouter(prefix="/api/admin", tags=["admin"])

_db = None


def init(db):
    global _db
    _db = db


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
