# AMEO - Asteroid Monitoring & Earth Orbit

A professional, full-stack **asteroid monitoring and Earth orbit dashboard** built with live NASA NeoWs data. Features real-time NEO ingestion, a custom orbital mechanics physics engine, Monte Carlo uncertainty visualization, a 3D interactive solar-system scene, and WebSocket-based impact alerts.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Docker Compose                          │
│                                                                │
│  ┌──────────────────┐      ┌─────────────────────────────────┐ │
│  │   React/Vite     │      │          FastAPI                │ │
│  │   (port 5173)    │◄────►│          (port 8000)           │ │
│  │                  │      │                                 │ │
│  │ • React Three    │      │ • REST endpoints (asyncpg)      │ │
│  │   Fiber (3D)     │      │ • WebSocket alerts              │ │
│  │ • Recharts       │      │ • APScheduler (15-min poll)     │ │
│  │ • Zustand        │      │ • Physics Engine (pure Python)  │ │
│  │ • Axios / WS     │      │                                 │ │
│  └──────────────────┘      └────────────┬────────────────────┘ │
│                                         │                      │
│                            ┌────────────┴───────────┐          │
│                            │  PostgreSQL  │  Redis   │          │
│                            │  (5432)      │  (6379)  │          │
│                            └─────────────────────────┘          │
└────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| **Live NEO Feed** | Polls NASA NeoWs every 15 min via APScheduler; sortable/filterable table |
| **PHA Highlighting** | Potentially Hazardous Asteroids get distinct risk-tier badges (LOW→CRITICAL) |
| **Custom Physics Engine** | Keplerian elements, RK4 propagator, Monte Carlo (N=500–1000) |
| **3D Orbital Visualizer** | React Three Fiber scene: Sun, Earth, up to 10 NEO orbit lines, clickable |
| **Time Scrubber** | Animate orbital positions ±30 days with play/pause |
| **Monte Carlo Corridors** | Uncertainty distribution histogram, 5th/95th percentile bounds |
| **Risk Leaderboard** | Ranked composite score: proximity × size × velocity × uncertainty |
| **WebSocket Alerts** | Real-time push when NEO crosses <5 LD; persistent alert log |
| **OpenAPI Docs** | Auto-generated at `http://localhost:8000/docs` |
| **Docker Compose** | One command brings up the full stack |

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A free [NASA API key](https://api.nasa.gov/) (optional — `DEMO_KEY` works for testing)

### 1. Clone & configure

```bash
git clone https://github.com/ameer06/AMEO-Asteroid-Monitoring-Earth-Orbit-.git
cd AMEO-Asteroid-Monitoring-Earth-Orbit-

cp .env.example .env
# Edit .env and set NASA_API_KEY=your_key_here
```

### 2. Launch with Docker Compose

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 3. Local development (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Start PostgreSQL + Redis locally, then:
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
pip install pytest
pytest tests/ -v
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/neos` | Paginated list (filters: `hazardous_only`, `sort_by`, `sort_dir`, `page`, `limit`) |
| `GET` | `/neos/{id}` | Full NEO detail |
| `GET` | `/neos/{id}/orbit` | Keplerian elements + RK4-propagated 300-point orbit path |
| `GET` | `/neos/{id}/montecarlo` | Monte Carlo uncertainty corridor (N=500 runs) |
| `GET` | `/neos/{id}/history` | Historical close approach records |
| `GET` | `/alerts/log` | Persisted alert event log |
| `WS`  | `/alerts/ws` | Real-time WebSocket stream |
| `GET` | `/health` | Service health check |

Full interactive docs: **http://localhost:8000/docs**

---

## Physics Engine

Located in `backend/physics/orbital_mechanics.py` — importable independently, no third-party astro libraries.

### Components

**`state_to_keplerian(r, v)`**
Converts Cartesian position/velocity vectors to Keplerian orbital elements `{a, e, i, Ω, ω, M, T}`.

**`keplerian_to_state(a, e, i, Ω, ω, M)`**
Inverse transform. Solves Kepler's equation via Newton-Raphson. Uses full 3D rotation matrix (perifocal → ECI).

**`propagate_orbit(..., days, steps)`**
RK4 two-body integrator under solar gravity. Returns `steps+1` `{t, x, y, z}` points in AU.

**`monte_carlo_approach(... n_runs=1000)`**
Perturbs initial position (σ=100 km) and velocity (σ=10 m/s) across N runs. Returns mean/std/percentile miss distances and a spatial corridor.

**`closest_approach(...)`**
Brute-force minimum distance finder over the propagated trajectory.

### Test Verification

```bash
pytest tests/test_orbital_mechanics.py -v
```

Tests verify:
- Earth orbit at ~1 AU
- Keplerian round-trip accuracy < 1e-4
- Earth orbital velocity ~30 km/s
- Circular orbit energy conservation (< 1% radius drift)
- Monte Carlo percentile ordering
- Risk score monotonicity

---

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Pydantic settings
│   ├── database.py          # asyncpg session factory
│   ├── scheduler.py         # APScheduler 15-min poll
│   ├── models/
│   │   └── neo.py           # SQLAlchemy ORM: NEO, CloseApproach, AlertLog
│   ├── services/
│   │   ├── nasa_client.py   # httpx NASA API client
│   │   └── neo_service.py   # Business logic layer
│   ├── routers/
│   │   ├── neos.py          # REST endpoints
│   │   └── alerts.py        # WebSocket + alert log
│   ├── physics/
│   │   ├── orbital_mechanics.py  # Custom physics engine
│   │   └── risk_scorer.py        # Composite risk scoring
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css        # Full design system
│   │   ├── api/neoApi.js    # Axios + WebSocket client
│   │   ├── store/neoStore.js # Zustand global state
│   │   └── components/
│   │       ├── OrbitalScene.jsx   # React Three Fiber 3D
│   │       ├── NEOTable.jsx       # Sortable data table
│   │       ├── RiskLeaderboard.jsx
│   │       ├── DetailPanel.jsx    # Elements + MC + history charts
│   │       ├── AlertBanner.jsx    # WebSocket toasts
│   │       └── TimeScrubber.jsx   # 30-day animation
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.js
├── tests/
│   └── test_orbital_mechanics.py
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Portfolio Story

> *"Built a meteor tracker, then extended the physics pipeline to full NEO risk analysis."*

**Differentiators:**
- ✅ Monte Carlo uncertainty in 3D — rare in portfolio projects
- ✅ Custom two-body physics engine verifiable against NASA data
- ✅ WebSocket real-time alerting — beyond request/response
- ✅ Docker Compose full-stack — production-ready deployment
- ✅ Clean layer separation: Route → Service → Physics → DB

---

## Deploy live

See **[DEPLOY.md](./DEPLOY.md)** for GitHub push steps and one-click deploy on [Render](https://render.com) using `render.yaml`.

---

## License

MIT
