from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/sources", tags=["sources"])

_db = None
_scraper = None
_scheduler = None


def init(db, scraper, scheduler):
    global _db, _scraper, _scheduler
    _db = db
    _scraper = scraper
    _scheduler = scheduler


class SourceRequest(BaseModel):
    name: str
    url: str
    type: str = "rss"   # "rss" or "page"


@router.get("")
async def list_sources():
    return {"sources": _db.list_sources()}


@router.post("")
async def add_source(req: SourceRequest, background: BackgroundTasks):
    src_id = _db.add_source(req.name, req.url, req.type)
    if src_id:
        source = {"id": src_id, "name": req.name, "url": req.url, "type": req.type}
        background.add_task(_learn_one, source)
    return {"ok": True, "id": src_id}


@router.delete("/{source_id}")
async def delete_source(source_id: int):
    from core import vectorstore
    import config
    vectorstore.delete_by_source(source_id)
    _db.delete_source(source_id)
    return {"ok": True}


@router.patch("/{source_id}/toggle")
async def toggle_source(source_id: int, enabled: bool):
    _db.toggle_source(source_id, enabled)
    return {"ok": True}


@router.post("/refresh")
async def refresh_all(background: BackgroundTasks):
    background.add_task(_scheduler.trigger_now)
    return {"ok": True, "message": "Learning started in background"}


def _learn_one(source: dict):
    count = _scraper.learn_from_source(source)
    _db.update_source_fetch(source["id"], count)
    _db.log_learning(source["name"], count)
