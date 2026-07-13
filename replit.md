# CJ-AI — Cybersecurity AI Assistant

A bilingual (Arabic/English) cybersecurity AI assistant using a RAG (Retrieval-Augmented Generation) architecture. Provides context-aware answers on penetration testing, malware analysis, and information security, with a strict "cybersecurity-only" scope guard.

## Project structure

```
cj-web/
  backend/    FastAPI server, RAG pipeline, scrapers (port 8000)
  frontend/   React 18 + Vite UI (port 5173)
cj-ai/        Terminal/CLI version of the assistant
```

## How to run

Two workflows must both be running:

| Workflow | Command | Port |
|---|---|---|
| Backend (FastAPI) | `cd cj-web/backend && python main.py` | 8000 |
| Frontend (Vite) | `cd cj-web/frontend && npm run dev` | 5173 |

The frontend proxies API calls to the backend. Open the app on port **5173**.

## Required secrets

All set as Replit Secrets:

| Secret | Purpose |
|---|---|
| `SESSION_SECRET` | JWT signing key |
| `GROQ_API_KEY` | Groq LLM (llama-3.3-70b-versatile) |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |

## Tech stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, APScheduler
- **Frontend:** React 18, Vite, react-markdown
- **LLM:** Groq (`llama-3.3-70b-versatile`)
- **Vector DB:** Qdrant Cloud with `all-MiniLM-L6-v2` embeddings (fastembed/ONNX)
- **Auth:** JWT (30-day tokens), bcrypt passwords, SQLite session storage
- **Auto-learning:** RSS scraper runs every 6 h (Hacker News, Krebs, SANS, SecurityWeek, NVD, BleepingComputer)

## Admin

Default admin username: `249shadow` (override with `ADMIN_USERNAME` secret). Admin endpoints are at `/api/admin/`.

## User preferences
