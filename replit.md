# CJ-AI — Cybersecurity AI Assistant

An Arabic/English cybersecurity AI chat assistant built with a RAG (Retrieval-Augmented Generation) architecture. Users register/login and ask questions about penetration testing, malware analysis, networking, CTF challenges, and more.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn (port 8000) |
| Frontend | React + Vite (port 5173) |
| Vector DB | Qdrant Cloud |
| LLM | Groq (llama-3.3-70b-versatile) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Auth | JWT (bcrypt passwords, 30-day tokens) |
| Storage | SQLite (`cj-web/backend/data/cj_web.db`) |

## Running on Replit

Two workflows must both be running:

- **Backend (FastAPI):** `cd cj-web/backend && python main.py` → port 8000
- **Frontend (Vite):** `cd cj-web/frontend && npm run dev` → port 5173

The frontend proxies `/api/*` to the backend, so the preview pane runs on port **5173**.

## Required Secrets

| Secret | Where to get it |
|---|---|
| `QDRANT_URL` | Qdrant Cloud dashboard |
| `QDRANT_API_KEY` | Qdrant Cloud dashboard |
| `GROQ_API_KEY` | console.groq.com |
| `SESSION_SECRET` | Any random string (already set) |

## Project Structure

```
cj-ai/          # Knowledge base (knowledge.json) + CLI core
cj-web/
  backend/      # FastAPI app — api/, core/, database/, utils/
  frontend/     # React app — src/components/, src/api.js
```

## User Preferences

- Keep existing project structure and stack unchanged unless explicitly asked.
