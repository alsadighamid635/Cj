"""
CJ-AI Web — FastAPI backend entry point.

Startup sequence:
  1. Validate required environment variables (fail fast, clear error)
  2. Initialise the SQLite database and run schema migrations
  3. Seed the Q&A knowledge base into Qdrant (idempotent)
  4. Seed default RSS sources into the DB (idempotent)
  5. Wire all API routers with shared dependencies
  6. Start the background learning scheduler
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import config
from database.db import Database
from core import seeder, scraper, scheduler
from core.rag import RAGPipeline
from utils.logger import setup_logger
from api import auth as auth_router
from api import chat as chat_router
from api import sources as sources_router
from api import admin as admin_router

# ── Logger must be set up before anything else logs ───────────────────────────
logger = setup_logger(config.LOG_FILE)

# ── Fail fast if required secrets are missing ─────────────────────────────────
config.validate_required_env()

db = Database(config.DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    db.initialize()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-load the embedding model so the first user request is instant
    from core import vectorstore
    vectorstore.warm_up()

    seeder.seed_knowledge()

    for feed in config.DEFAULT_FEEDS:
        db.add_source(feed["name"], feed["url"], "rss")

    pipeline = RAGPipeline(db)
    auth_router.init(db)
    chat_router.init(pipeline, db)
    sources_router.init(db, scraper, scheduler)
    admin_router.init(db)

    scheduler.start(db, scraper)

    logger.info("CJ-AI Web started successfully.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    scheduler.stop()
    db.close()
    logger.info("CJ-AI Web shut down.")


app = FastAPI(title="CJ-AI Web", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(sources_router.router)
app.include_router(admin_router.router)

# ── Serve the pre-built React frontend (production only) ─────────────────────
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
