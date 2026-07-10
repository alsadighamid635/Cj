"""
CJ-AI Web — FastAPI backend
Serves the REST API on /api/* and the React frontend on /*
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import config
from database.db import Database
from core import seeder, scraper, scheduler
from core.rag import RAGPipeline
from utils.logger import setup_logger
from api import chat as chat_router
from api import sources as sources_router
from api import admin as admin_router

logger = setup_logger(config.LOG_FILE)

db = Database(config.DB_FILE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    db.initialize()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Seed built-in knowledge into ChromaDB (runs only if empty)
    seeder.seed_knowledge()

    # Seed default RSS sources into DB if not already present
    for feed in config.DEFAULT_FEEDS:
        db.add_source(feed["name"], feed["url"], "rss")

    # Wire API modules
    pipeline = RAGPipeline(db)
    chat_router.init(pipeline, db)
    sources_router.init(db, scraper, scheduler)
    admin_router.init(db)

    # Start background learning scheduler
    scheduler.start(db, scraper)

    logger.info("CJ-AI Web started.")
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    scheduler.stop()
    db.close()


app = FastAPI(title="CJ-AI Web", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router.router)
app.include_router(sources_router.router)
app.include_router(admin_router.router)

# Serve the built React frontend
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Mount /assets directory for JS/CSS bundles
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Explicitly serve PWA root files so they are not swallowed by the SPA fallback
    _ROOT_FILES = {"manifest.json", "favicon.svg", "favicon.ico", "robots.txt", "sw.js"}

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        filename = full_path.lstrip("/")
        if filename in _ROOT_FILES:
            candidate = FRONTEND_DIST / filename
            if candidate.exists():
                return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
