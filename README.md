# CJ-AI — Cybersecurity AI Assistant

An Arabic/English cybersecurity AI assistant built with a RAG (Retrieval-Augmented Generation) architecture. Users can ask questions about penetration testing, malware analysis, networking, CTF challenges, and more — and receive accurate, context-aware answers in their language.

---

## Live Demo

- **Frontend (Vercel):** https://cj-ww1u.onrender.com *(see Vercel project)*
- **Backend (Render):** https://cj-ww1u.onrender.com

---

## Features

| Feature | Description |
|---------|-------------|
| 🤖 Groq LLM | Llama 3.3 70B answers questions with RAG context |
| 🔍 Vector Search | Qdrant Cloud stores and searches 60+ Q&A entries + scraped articles |
| 🌐 Bilingual | Automatically detects Arabic or English and responds accordingly |
| 📰 Auto-learning | Background scheduler scrapes RSS feeds every 6 hours |
| 🛡️ Scope Guard | Politely declines non-cybersecurity questions |
| 💬 Session Memory | Conversation history stored in SQLite and used as LLM context |

---

## Architecture

```
User (React frontend)
        │
        ▼
FastAPI Backend  (/api/*)
        │
        ├── RAGPipeline
        │       ├── shell_ref      →  instant tool lookups (nmap, wireshark, …)
        │       ├── vectorstore    →  Qdrant Cloud (semantic search)
        │       └── generator      →  Groq LLM (llama-3.3-70b-versatile)
        │
        ├── Database (SQLite)      →  sessions, messages, sources, logs
        └── Scheduler (APScheduler) → RSS / webpage scraping every 6h
```

### Backend modules

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app, startup/shutdown lifecycle |
| `config.py` | All constants and environment variables |
| `core/rag.py` | End-to-end query pipeline (5-step flow) |
| `core/generator.py` | Groq LLM call with RAG context injection |
| `core/vectorstore.py` | Qdrant Cloud wrapper (add, search, delete) |
| `core/scraper.py` | RSS and webpage fetcher with SSRF protection |
| `core/seeder.py` | One-time Q&A knowledge seeding at startup |
| `core/scheduler.py` | Background APScheduler job |
| `core/security_filter.py` | Keyword-based scope guard |
| `core/shell_ref.py` | Static reference for common security tools |
| `database/db.py` | SQLite ORM (sessions, messages, sources) |
| `utils/logger.py` | Centralised logging |
| `utils/text.py` | Text normalization, chunking, language detection |
| `api/chat.py` | `POST /api/chat` and session management |
| `api/sources.py` | CRUD for learning sources |
| `api/admin.py` | Stats endpoint |

### Frontend components

| File | Responsibility |
|------|---------------|
| `App.jsx` | Root component — session state, message flow |
| `api.js` | Fetch wrapper for all backend calls |
| `components/ChatWindow.jsx` | Message list and loading indicator |
| `components/MessageBubble.jsx` | Individual message with Markdown rendering |
| `components/InputBar.jsx` | Auto-resizing textarea, keyboard handling |
| `components/Sidebar.jsx` | Session list, new chat, navigation |
| `components/SourcePanel.jsx` | Add/remove/refresh learning sources |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | [Groq](https://groq.com) — `llama-3.3-70b-versatile` |
| Vector DB | [Qdrant Cloud](https://qdrant.tech) — cosine similarity, 384-dim |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers, runs locally) |
| Backend | Python 3.11, FastAPI, Uvicorn, APScheduler |
| Database | SQLite with WAL mode |
| Frontend | React 18, Vite, react-markdown, react-syntax-highlighter |
| Hosting | Render (backend) + Vercel (frontend) — both free tier |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Qdrant Cloud account (free tier)
- Groq API key (free tier)

### Setup

```bash
# Clone the repository
git clone https://github.com/alsadighamid635/Cj
cd Cj

# Backend
cd cj-web/backend
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key
export QDRANT_URL=your_cluster_url
export QDRANT_API_KEY=your_api_key

python main.py   # runs on http://localhost:8000

# Frontend (separate terminal)
cd cj-web/frontend
npm install --legacy-peer-deps
npm run dev      # runs on http://localhost:5173
```

---

## Deployment

### Backend → Render

1. Connect GitHub repo to Render → **New Web Service**
2. Root Directory: `cj-web/backend`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python main.py`
5. Add environment variables: `GROQ_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`
6. Enable **Auto-Deploy** in Settings

### Frontend → Vercel

1. Connect GitHub repo to Vercel → **New Project**
2. Root Directory: `cj-web/frontend`
3. Add environment variable: `VITE_API_URL=https://<your-render-url>`
4. Deploy — auto-deploys on every push to `main`

---

## RAG Query Flow

```
User question
      │
      ▼
1. Shell reference lookup  ──► known tool? → return instantly
      │ no
      ▼
2. Qdrant vector search    ──► retrieve top-6 relevant chunks
      │
      ▼
3. Groq LLM generation     ──► answer with context + history
      │
      ▼
4. Scope guard             ──► cybersecurity? → if not, decline politely
      │
      ▼
5. Persist to SQLite + Qdrant chat memory
```

---

## Project Structure

```
Cj/
├── cj-ai/
│   └── knowledge/
│       └── knowledge.json     # 60 seeded cybersecurity Q&A entries
├── cj-web/
│   ├── backend/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── requirements.txt
│   │   ├── api/               # FastAPI routers
│   │   ├── core/              # RAG, LLM, vectorstore, scraper
│   │   ├── database/          # SQLite layer
│   │   └── utils/             # logger, text helpers
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── api.js
│       │   └── components/
│       ├── public/
│       ├── vercel.json
│       └── vite.config.js
└── render.yaml                # Render deployment config
```

---

*Built by 249shadow — specialized in cybersecurity & information security.*
