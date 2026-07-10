---
name: CJ-AI Web stack
description: Runtime stack, key packages, and deployment targets for the CJ-AI web app.
---

## Stack

- **Backend**: FastAPI + Uvicorn on port `$PORT` (defaults 8000), Python 3.11
- **Vector DB**: Qdrant Cloud (qdrant-client 1.18) — replaces local ChromaDB
  - Collections: `cybersec_knowledge`, `cybersec_sources`, `chat_memory`
  - API: `query_points()` for search (NOT the old `search()`), `FilterSelector` for deletes
  - Cosine distance = `1.0 - r.score` (Qdrant returns similarity, old code expected distance)
- **LLM**: Groq `llama-3.3-70b-versatile` via `groq` package
- **Embeddings**: ChromaDB `DefaultEmbeddingFunction` (all-MiniLM-L6-v2, ONNX, local)
- **Frontend**: React 18 + Vite on port 5173, proxies `/api` to backend in dev

## Key env vars (all secrets)

- `GROQ_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`

## Deployment targets

- **Backend → Render**: `render.yaml` at repo root; `startCommand: python main.py`; port read from `$PORT`
- **Frontend → Vercel**: root dir = `cj-web/frontend`; `VITE_API_URL` = Render backend URL; `vercel.json` handles SPA routing

## Why

Migrated from local ChromaDB to Qdrant Cloud so data persists across Render restarts (ephemeral filesystem). Groq chosen for free tier + speed.

## How to apply

- Any new vector operation: use `query_points()` not `search()`; delete uses `FilterSelector(filter=Filter(...))`
- Port binding: always read `int(os.environ.get("PORT", 8000))` in `main.py`
- Qdrant errors should propagate (no silent swallowing in `count()`) so startup fails clearly
