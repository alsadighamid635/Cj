---
name: CJ-AI Web stack
description: FastAPI+Qdrant backend (8000) + React/Vite frontend (5173); real JWT per-user auth; language system; admin page.
---

## Stack
- Backend: FastAPI + Uvicorn on port 8000 (`cj-web/backend/main.py`)
- Frontend: React + Vite on port 5173 (`cj-web/frontend/`)
- Vector DB: Qdrant Cloud (QDRANT_URL + QDRANT_API_KEY secrets)
- LLM: Groq (GROQ_API_KEY secret)
- Auth: JWT (SESSION_SECRET), bcrypt passwords, 30-day tokens

## Language system
- Arabic is the default language (RTL). English is the toggle option.
- Translations live in `src/i18n.js` (T.ar / T.en objects).
- Language context in `src/context/LangContext.jsx` — persists to localStorage under `cj_lang`.
- Sets `document.documentElement.dir` + `document.documentElement.lang` on change.
- All components consume `useLang()` → `{ t, lang, setLang }`.

## Auth / Remember Me
- `setToken(token, remember)` in `api.js`:
  - remember=true → localStorage (persists across browser restarts)
  - remember=false → sessionStorage (clears on tab/browser close)
- `getToken()` checks localStorage first, then sessionStorage.

## Admin page
- Only visible to the user whose username matches `config.ADMIN_USERNAME` (defaults to `249shadow`).
- Backend: `GET /api/admin/users` in `api/admin.py` — uses `_require_admin` dependency that checks username against `ADMIN_USERNAME`.
- Frontend: `AdminPage.jsx` — overlay modal showing all registered users.
- Admin button shows in topbar only when `user.username === ADMIN_USERNAME`.
- To change admin username: set `ADMIN_USERNAME` env var and update `ADMIN_USERNAME` constant in `App.jsx`.

## OG link-preview
- Needs prod domain after deploy (currently hardcoded to Render URL in frontend).
