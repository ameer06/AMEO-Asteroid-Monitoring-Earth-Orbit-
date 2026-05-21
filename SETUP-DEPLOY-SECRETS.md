# Finish deploy (one-time, ~10 minutes)

Code is on GitHub. **Render / Neon / Vercel need your login** — complete these tabs in order.

## 1. Neon (free database)

1. Open [neon.tech](https://neon.tech) → sign up → **New project** `ameo`.
2. Copy **connection string** (pooled, `postgresql://...`).

## 2. Render (API + dashboard)

1. Open:  
   **https://render.com/deploy?repo=https://github.com/ameer06/AMEO-Asteroid-Monitoring-Earth-Orbit-**
2. Connect GitHub if asked → apply blueprint.
3. When prompted for env vars:

   | Variable | Value |
   |----------|--------|
   | `NASA_API_KEY` | From [api.nasa.gov](https://api.nasa.gov/) |
   | `DATABASE_URL` | Neon string from step 1 |
   | `CORS_ORIGINS` | Leave blank first; set after step 2 finishes |

4. Wait until **ameo-api** and **ameo-web** are **Live**.
5. Open **ameo-web** URL → copy it.
6. On **ameo-api** → Environment → set `CORS_ORIGINS` to that URL → **Save & redeploy**.

Your live app: **ameo-web** URL on Render.

## 3. Optional — Vercel frontend (GitHub Actions)

Only if you want the UI on Vercel instead of Render:

1. [vercel.com](https://vercel.com) → import repo → root `frontend` → add `VITE_API_URL` = your `ameo-api` URL.
2. GitHub repo → **Settings → Secrets → Actions** → add:

   | Secret | Where to get it |
   |--------|------------------|
   | `VERCEL_TOKEN` | Vercel → Account → Tokens |
   | `VERCEL_ORG_ID` | Vercel project → Settings → General |
   | `VERCEL_PROJECT_ID` | Same page |
   | `VITE_API_URL` | `https://ameo-api-xxxx.onrender.com` |

3. Push to `main` or run workflow **Deploy frontend to Vercel** manually.

Update Render `CORS_ORIGINS` to include the Vercel URL.
