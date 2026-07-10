---
name: CJ-AI Web stack
description: Architecture and run instructions for the cj-web full-stack project.
---

## Stack
- Backend: FastAPI + ChromaDB (RAG) + APScheduler, runs on port 8000 (`cd cj-web/backend && python main.py`)
- Frontend: React + Vite (PWA), runs on port 5173 (`cd cj-web/frontend && npm run dev`), proxies `/api/*` to backend
- ChromaDB: persistent at `cj-web/backend/data/chroma/` — three collections: cybersec_knowledge, cybersec_sources, chat_memory
- SQLite: `cj-web/backend/data/cj_web.db` — sessions, messages, sources, unanswered

## Startup sequence
1. Backend seeds knowledge.json into ChromaDB on first run (only if collection is empty)
2. Backend seeds DEFAULT_FEEDS into sources table
3. APScheduler fetches RSS feeds every 6h in background
4. Frontend dev server proxies /api/* to http://127.0.0.1:8000

## Key decisions
- RAG search happens before scope filter (same pattern as cj-ai terminal app)
- ChromaDB uses DefaultEmbeddingFunction (ONNX all-MiniLM-L6-v2, ~79MB, downloaded on first run)
- No external LLM API — responses are extracted/formatted from retrieved chunks

**Why local-only:** user explicitly chose "محلي بالكامل" (fully local, no API).
