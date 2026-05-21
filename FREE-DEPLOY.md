# Deploy 100% free (long-term)

Render’s **built-in free Postgres is deleted after 30 days**. That is not “totally free forever.”

Use this **3-service $0 stack** instead (all have free tiers with no 30-day DB wipe):

| Piece | Platform | Cost |
|-------|----------|------|
| Database | [Neon](https://neon.tech) | $0 |
| API + scheduler | [Render](https://render.com) free web service | $0 (sleeps when idle) |
| Dashboard UI | Render static **or** [Vercel](https://vercel.com) | $0 |

You need: GitHub repo + NASA API key (free).

---

## Step 1 — Free database (Neon)

1. Sign up at [neon.tech](https://neon.tech) (GitHub login is fine).
2. **New project** → name it `ameo` → region closest to you.
3. Open **Connection details** → copy the **pooled** connection string  
   (starts with `postgresql://...`).
4. Keep it secret — this is your `DATABASE_URL` for the API.

Neon free tier is for dev/portfolio; it has size limits but **does not expire in 30 days** like Render’s free Postgres.

---

## Step 2 — API on Render (no Render database)

1. [render.com](https://render.com) → **New → Blueprint**.
2. Connect repo `AMEO-Asteroid-Monitoring-Earth-Orbit-`.
3. When asked for blueprint file, use **`render-free.yaml`** (not `render.yaml`).
4. Set environment variables when prompted:

   | Variable | Value |
   |----------|--------|
   | `NASA_API_KEY` | Your key from [api.nasa.gov](https://api.nasa.gov/) |
   | `DATABASE_URL` | Neon connection string from Step 1 |
   | `CORS_ORIGINS` | Leave empty for now; fill after Step 3 |

5. Wait for **ameo-api** to deploy. Copy its URL:  
   `https://ameo-api-xxxx.onrender.com`

**Note:** Free Render services **spin down** after ~15 minutes idle. First visit after sleep takes ~30–60 seconds. That is normal on $0.

---

## Step 3 — Frontend (pick one)

### Option A — Render (same blueprint)

`render-free.yaml` also creates **ameo-web**. After deploy, open that URL.

Set on **ameo-api**:

```text
CORS_ORIGINS=https://ameo-web-xxxx.onrender.com
```

Redeploy the API.

### Option B — Vercel (often faster UI)

1. [vercel.com](https://vercel.com) → import repo.
2. **Root Directory:** `frontend`
3. Env: `VITE_API_URL` = `https://ameo-api-xxxx.onrender.com`
4. Deploy → copy Vercel URL.
5. On Render **ameo-api**, set:

```text
CORS_ORIGINS=https://your-app.vercel.app
```

Redeploy API.

---

## Step 4 — Verify

- Open your **frontend** URL.
- Status should show **Live** (not Demo) after the API wakes up.
- API docs: `https://ameo-api-xxxx.onrender.com/docs`
- First NASA poll runs on API startup; table may take a minute to fill.

---

## What is actually free vs not

| | Free? |
|--|--------|
| Money | **$0** if you stay on free tiers |
| Always instant | **No** — Render API sleeps when idle |
| Unlimited traffic | **No** — bandwidth/CPU limits on free tiers |
| Forever guarantee | **No** — providers can change terms; Neon/Render/Vercel can update limits |

This is the best realistic **$0 full app** setup for your project without paying.

---

## Option 2 — One server, $0 (harder)

**Oracle Cloud Always Free** VM → install Docker → `docker compose up -d`.

- Truly one place for UI + API + Postgres
- No 30-day DB delete
- More setup (SSH, firewall, Docker)

Search: “Oracle Cloud Ampere free tier docker compose” when you are ready for that path.

---

## Do NOT use for long-term free

| Setup | Why |
|-------|-----|
| `render.yaml` with Render Postgres | DB **gone after 30 days** |
| Railway only | ~**$1/month** credit, runs out |
| Vercel only | Demo mode, no real NASA/DB backend |

---

## Quick reference

```text
Neon     →  DATABASE_URL
Render   →  ameo-api (FastAPI)
Render or Vercel  →  frontend + VITE_API_URL + CORS_ORIGINS
```
