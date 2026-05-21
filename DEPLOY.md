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

## 2. Deploy on Render (recommended, free tier)

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

## 3. Local Docker (same as production stack)

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
| `VITE_API_URL` | Frontend build | API base URL (set automatically on Render) |

---

## Troubleshooting

- **Demo mode only** — API unreachable or CORS blocked; check `VITE_API_URL` and `CORS_ORIGINS`.
- **Empty NEO table** — Wait for the first NASA poll after API startup, or check API logs on Render.
- **WebSocket offline** — Confirm `CORS_ORIGINS` includes the frontend URL; alerts still work via REST.
