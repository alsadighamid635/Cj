---
name: CJ-AI Web stack
description: Stack, ports, auth, production URLs, and database setup for CJ-AI Web.
---

## Stack
- FastAPI + PostgreSQL backend on port 8000 (dev) / Render (prod)
- React/Vite frontend on port 5173 (dev) / Vercel (prod)
- Real JWT per-user auth (30-day tokens, bcrypt passwords)
- Vector store: Qdrant Cloud (persistent, separate from user DB)

## Production URLs
- Frontend (Vercel): https://frontend-livid-three-77.vercel.app
- Backend (Render): https://cj-ww1u.onrender.com
- Render service ID: srv-d98fasetrd3s73eielbg

## Database
- **PostgreSQL via Neon** (persistent, survives Render restarts/redeploys)
- Secret key: DATABASE_URL (set in both Replit Secrets and Render env vars)
- db.py uses psycopg2 ThreadedConnectionPool (minconn=1, maxconn=10)
- Migrated FROM SQLite (ephemeral on Render free tier) TO PostgreSQL
- **Why:** Render free tier wipes local filesystem on every restart — SQLite was losing all user accounts and chat history on each deploy.

## Deployment notes
- Vercel must use `yarn` — npm has an "Exit handler never called" bug on Vercel's build infra
- vercel.json: `installCommand: "yarn install"`, `buildCommand: "yarn build"`
- VITE_API_URL set on Vercel project pointing to Render backend
- Render env vars: SESSION_SECRET, GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY, DATABASE_URL
- Auto-deploy on both platforms from GitHub main branch (repo: github.com/alsadighamid635/Cj)
- OG image: /og-image.jpg in frontend/public (4096x3121 JPEG)
