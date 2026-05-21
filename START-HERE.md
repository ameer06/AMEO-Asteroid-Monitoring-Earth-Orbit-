# Deploy in 5 minutes (copy-paste only)

Your UI is already live: **https://frontend-lac-zeta-37.vercel.app**

You only need to start the **API on Render** and paste 2 values.

---

## Step 1 — NASA key (1 minute)

1. Open https://api.nasa.gov/index.html
2. Click **Generate API Key** → fill the short form → submit.
3. Copy the key from your email or the page (looks like `abc123...`).

---

## Step 2 — Deploy on Render (3 minutes)

1. Open this link (logged in with GitHub):

   **https://render.com/deploy?repo=https://github.com/ameer06/AMEO-Asteroid-Monitoring-Earth-Orbit-**

2. Blueprint name: anything (e.g. `ameo-astro`).

3. Select **“Create all as new services”** (not “Associate existing”).

4. You should see **ameo-api** and **ameo-web**. Click **Deploy Blueprint**.

5. Render will ask for missing values. Paste:

   | Name | Paste this |
   |------|------------|
   | `NASA_API_KEY` | Your NASA key from Step 1 |
   | `DATABASE_URL` | Your Neon connection string from Neon dashboard |

   (`CORS_ORIGINS` is already set for your Vercel site.)

6. Wait until **ameo-api** shows **Live** (green). First time can take 5–10 minutes.

7. Click **ameo-api** → copy the URL at the top (e.g. `https://ameo-api-xxxx.onrender.com`).

---

## Step 3 — Connect Vercel to the API (2 minutes)

1. Open https://vercel.com/ameer06s-projects/frontend/settings/environment-variables

2. Add variable:

   | Name | Value |
   |------|--------|
   | `VITE_API_URL` | Your **ameo-api** URL (no `/` at the end) |

   Environment: **Production** → Save.

3. Open https://vercel.com/ameer06s-projects/frontend/deployments

4. Click **⋯** on the latest deployment → **Redeploy** → **Redeploy**.

---

## Done

Open **https://frontend-lac-zeta-37.vercel.app**

- Top bar should say **Live** (not Demo).
- First load after idle API may take ~30 seconds.

API docs: `https://YOUR-ameo-api-URL.onrender.com/docs`

---

## If you get stuck

Tell me:

1. Screenshot or text of what Render shows under **ameo-api** (Building / Failed / Live).
2. Your **ameo-api** URL after deploy.

I can fix errors from logs — you only paste URLs, not passwords.

---

## Security

You shared your Neon password in chat earlier. After everything works:

Neon → **Reset password** → update `DATABASE_URL` on Render.
