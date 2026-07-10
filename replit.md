# CJ-AI Web

**ذكاء اصطناعي متخصص في أمن المعلومات** — A cybersecurity-focused AI assistant (Arabic/English) with a RAG pipeline, RSS news ingest, and a chat interface.

## Stack

- **Backend**: FastAPI + ChromaDB (RAG/vector store) + SQLite, running on port 8000
- **Frontend**: React 18 + Vite, running on port 5173 (proxies `/api` to backend)
- **Embeddings**: `all-MiniLM-L6-v2` via ChromaDB's default embedding function (ONNX)

## How to run

Two workflows are configured:

| Workflow | Command | Port |
|---|---|---|
| Backend (FastAPI) | `cd cj-web/backend && python main.py` | 8000 |
| Frontend (Vite) | `cd cj-web/frontend && npm run dev` | 5173 |

Start both from the Workflows panel. The frontend dev server proxies `/api/*` to the backend.

## Key directories

```
cj-web/
  backend/
    main.py          # FastAPI entry point + lifespan wiring
    config.py        # Paths, thresholds, RSS feeds, keyword list
    api/             # chat, sources, admin routers
    core/            # RAG pipeline, scraper, scheduler, vectorstore, seeder
    database/        # SQLite wrapper (conversations, sources)
    data/            # SQLite DB + ChromaDB persistent storage
  frontend/
    src/
      components/    # ChatWindow, InputBar, MessageBubble, Sidebar, SourcePanel
      api.js         # Fetch helpers for /api/*
```

## Deployment (Step-by-Step)

### Backend → Render (free)
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Render auto-detects `render.yaml` — just add the three env vars in the dashboard:
   - `GROQ_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
4. Deploy. Note your backend URL (e.g. `https://cj-ai-backend.onrender.com`)

### Frontend → Vercel (free)
1. Go to [vercel.com](https://vercel.com) → New Project → import your repo
2. Set **Root Directory** to `cj-web/frontend`
3. Add environment variable:
   - `VITE_API_URL` = your Render backend URL (no trailing slash)
4. Deploy

> `vercel.json` is already configured for SPA routing.
> The free Render tier sleeps after 15 min inactivity — first request may take ~30s to wake.

---

## LLM Integration

- **Provider**: Groq (`llama-3.3-70b-versatile`) — requires `GROQ_API_KEY` secret
- Groq is called in `cj-web/backend/core/generator.py` → `build_response()`
- Retrieved RAG chunks are injected as `## CONTEXT` into the system prompt
- Last 6 conversation turns are passed as message history for multi-turn awareness
- Language auto-detected (Arabic/English) — system prompt switches accordingly
- Falls back to direct chunk formatting if Groq is unavailable

## Notes

- The backend seeds 60 built-in Q&A entries into ChromaDB on first startup (from `cj-ai/knowledge/knowledge.json` if present; the app skips seeding gracefully if the file is missing).
- ChromaDB stores embeddings locally at `cj-web/backend/data/chroma/`. If you upgrade the `chromadb` package across a major version, delete that directory so it reinitialises cleanly.
- The installed `chromadb` version is **0.5.23** (the latest 1.x builds are currently blocked by the Replit package firewall).
- RSS learning runs every 6 hours via APScheduler (configurable in `config.py`).

## User preferences

<!-- Add user preferences here as they are expressed -->
