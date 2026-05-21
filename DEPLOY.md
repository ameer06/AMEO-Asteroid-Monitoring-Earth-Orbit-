# Deploy AMEO live

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: AMEO NEO dashboard"
git branch -M main
git remote add origin https://github.com/ameer06/AMEO-Asteroid-Monitoring-Earth-Orbit-.git
git push -u origin main
```

If the remote already exists, use `git remote set-url origin <url>` instead of `add`.

---

## 2. Deploy on Render (quick start)

> **Want $0 long-term?** Render’s free Postgres **expires after 30 days**.  
> Use **[FREE-DEPLOY.md](./FREE-DEPLOY.md)** + **`render-free.yaml`** (Neon DB + Render API + UI).

## 2b. Deploy on Render (includes 30-day free DB)

1. Sign in at [render.com](https://render.com) and connect your GitHub account.
2. **New → Blueprint** → select repo `AMEO-Asteroid-Monitoring-Earth-Orbit-`.
3. Render reads `render.yaml` and creates:
   - **ameo-db** — PostgreSQL
   - **ameo-api** — FastAPI (Docker)
   - **ameo-web** — React static site
4. When prompted, set **NASA_API_KEY** (get one at [api.nasa.gov](https://api.nasa.gov/)).
5. After the first deploy, open the **ameo-web** URL (your live dashboard).
6. Set **CORS_ORIGINS** on **ameo-api** to your frontend URL, e.g.  
   `https://ameo-web-xxxx.onrender.com`  
   (comma-separated if you add more origins). Redeploy the API service.

**Live URLs**

| Service | Example |
|---------|---------|
| Dashboard | `https://ameo-web-xxxx.onrender.com` |
| API docs | `https://ameo-api-xxxx.onrender.com/docs` |

Free tier services **spin down after inactivity**; the first load may take ~30s.

---

## 3. Vercel (frontend only)

Vercel is a strong fit for the **React/Vite UI**, but **not** for the full stack as-is:

| Part | Vercel? | Why |
|------|---------|-----|
| React dashboard | Yes | Static/Vite deploy, CDN, custom domain |
| FastAPI + Postgres | No (use Render/Railway/Fly) | Needs long-running process, DB, 15‑min scheduler |
| WebSocket alerts | Partial | Browser connects to **API host**, not Vercel; API must allow your Vercel URL in CORS |
| Docker Compose | No | Vercel does not run `docker-compose` |

**Recommended:** deploy **API + DB on Render** (see §2), then put the **UI on Vercel** pointing at that API.

### Steps

1. Deploy **ameo-api** on Render first and copy its URL, e.g. `https://ameo-api-xxxx.onrender.com`.
2. On Render **ameo-api**, set `CORS_ORIGINS` to include your Vercel URL (you get it after step 4, or use `https://*.vercel.app` during testing).
3. Go to [vercel.com](https://vercel.com) → **Add New Project** → import  
   `AMEO-Asteroid-Monitoring-Earth-Orbit-`.
4. Configure the project:

   | Setting | Value |
   |---------|--------|
   | **Root Directory** | `frontend` |
   | **Framework Preset** | Vite |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |

5. **Environment variables** (Project → Settings → Environment Variables):

   | Name | Value |
   |------|--------|
   | `VITE_API_URL` | `https://ameo-api-xxxx.onrender.com` (no trailing slash) |

6. Deploy. Your live dashboard is the Vercel URL (e.g. `https://ameo-xxx.vercel.app`).

7. Update Render `CORS_ORIGINS` with that exact Vercel URL and redeploy the API.

`frontend/vercel.json` enables SPA routing (all routes → `index.html`).

**Without a backend URL:** the app still runs in **demo mode** (sample asteroids) if the API is unreachable.

---

## 4. Local Docker (same as production stack)

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:5173 — nginx proxies `/neos` and `/alerts` to the backend.

---

## Environment variables

| Variable | Where | Purpose |
|----------|--------|---------|
| `NASA_API_KEY` | API | NASA NeoWs (use a real key in production) |
| `DATABASE_URL` | API | Set automatically on Render from Postgres |
| `CORS_ORIGINS` | API | Frontend URL(s), comma-separated |
| `VITE_API_URL` | Frontend build (Render or Vercel) | API base URL, e.g. `https://ameo-api-xxxx.onrender.com` |

---

## Troubleshooting

- **Demo mode only** — API unreachable or CORS blocked; check `VITE_API_URL` and `CORS_ORIGINS`.
- **Empty NEO table** — Wait for the first NASA poll after API startup, or check API logs on Render.
- **WebSocket offline** — Confirm `CORS_ORIGINS` includes the frontend URL; alerts still work via REST.
