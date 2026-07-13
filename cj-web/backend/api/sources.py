"""
Learning-sources API — manage RSS feeds and web pages for knowledge acquisition.

Endpoints:
  GET    /api/sources              — list all configured sources
  POST   /api/sources              — add a new RSS feed or web page
  DELETE /api/sources/{id}         — remove a source and its stored vectors
  PATCH  /api/sources/{id}/toggle  — enable or disable a source
  POST   /api/sources/refresh      — trigger an immediate scraping run
"""

from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator

from utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/sources", tags=["sources"])

_db = None
_scraper = None
_scheduler = None

_ALLOWED_SCHEMES = {"http", "https"}


def init(db, scraper, scheduler) -> None:
    global _db, _scraper, _scheduler
    _db = db
    _scraper = scraper
    _scheduler = scheduler


# ── Models ────────────────────────────────────────────────────────────────────

class SourceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str  = Field(..., min_length=10, max_length=2048)
    type: str = Field(default="rss", pattern="^(rss|page)$")

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("Invalid URL.")
        if parsed.scheme not in _ALLOWED_SCHEMES:
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("URL must include a valid hostname.")
        return v


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_sources():
    return {"sources": _db.list_sources()}


@router.post("")
async def add_source(req: SourceRequest, background: BackgroundTasks):
    src_id = _db.add_source(req.name, req.url, req.type)
    if src_id:
        source = {"id": src_id, "name": req.name, "url": req.url, "type": req.type}
        background.add_task(_learn_one, source)
        logger.info("Added source '%s' (%s)", req.name, req.url)
    return {"ok": True, "id": src_id}


@router.delete("/{source_id}")
async def delete_source(source_id: int):
    from core import vectorstore
    vectorstore.delete_by_source(source_id)
    _db.delete_source(source_id)
    logger.info("Deleted source id=%d", source_id)
    return {"ok": True}


@router.patch("/{source_id}/toggle")
async def toggle_source(source_id: int, enabled: bool):
    _db.toggle_source(source_id, enabled)
    return {"ok": True}


@router.post("/refresh")
async def refresh_all(background: BackgroundTasks):
    background.add_task(_scheduler.trigger_now)
    return {"ok": True, "message": "Learning started in background"}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _learn_one(source: dict) -> None:
    """Fetch and index a single source (runs in a background thread)."""
    count = _scraper.learn_from_source(source)
    _db.update_source_fetch(source["id"], count)
    _db.log_learning(source["name"], count)
