---
name: CJ-AI Web stack
description: Stack layout and auth model for the CJ-AI Web (249Shadow AI) project.
---

FastAPI+ChromaDB/Qdrant backend on port 8000, React+Vite frontend on port 5173 (proxies /api to backend).

## Auth
Real per-user accounts (bcrypt password hash + JWT signed with the `SESSION_SECRET` secret), not the old
browser-generated `X-User-ID` header. `api/auth.py` exposes `require_user`, a FastAPI dependency other
routers use to scope data to the caller's account. `db.get_messages()` takes an optional `user_id` and
returns nothing if the session isn't owned by that user — always pass it when reading messages on behalf
of a specific caller, or you reopen the cross-account data leak this replaced.

**Why:** the original design explicitly documented client-supplied identity as "UX privacy, not a security
boundary" — any user could read another's chats by guessing a session id. Real auth was needed before this
was a safe multi-user app.

## Link preview (Open Graph)
`frontend/index.html` uses `%VITE_SITE_URL%/og-image.png` placeholders, filled in from `frontend/.env`
(`VITE_SITE_URL`) at Vite build/dev time. That value is the Repl's dev domain by default — must be updated
to the production domain in `.env` after publishing, or shared links keep pointing at the dev URL.
