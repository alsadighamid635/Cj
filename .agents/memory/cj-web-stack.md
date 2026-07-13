---
name: CJ-AI Web stack
description: Stack, ports, auth, and production deployment URLs for CJ-AI Web.
---

## Stack
- FastAPI + Qdrant backend on port 8000 (dev) / Render (prod)
- React/Vite frontend on port 5173 (dev) / Vercel (prod)
- Real JWT per-user auth (30-day tokens, bcrypt passwords, SQLite)
- OG link-preview needs prod domain after deploy

## Production URLs
- Frontend (Vercel): https://frontend-livid-three-77.vercel.app
- Backend (Render): https://cj-ww1u.onrender.com
- Render service ID: srv-d98fasetrd3s73eielbg

## Deployment notes
- Vercel must use `yarn` as install/build manager — npm has an "Exit handler never called" bug on Vercel's build environment
- vercel.json: `installCommand: "yarn install"`, `buildCommand: "yarn build"`
- VITE_API_URL is set on Vercel project (prj_Xb5KllnVd8Ya6GiaHKiIiZrh61f8) pointing to Render backend
- Render env vars (SESSION_SECRET, GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY) set via API
- Auto-deploy on both platforms from GitHub main branch (repo: github.com/alsadighamid635/Cj)

**Why yarn on Vercel:** npm's "Exit handler never called" is a known bug affecting certain npm+Node combos on Vercel's build infra. Yarn bypasses it completely.
