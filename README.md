# ⚽ World Cup 2026 Simulator

A full-stack Monte Carlo simulator for the FIFA World Cup 2026. It runs
1,000+ tournament simulations (group stage → knockouts), streams live progress
over a WebSocket, and renders an ESPN-style bracket with each team's
championship probability colour-coded by confidence level.

![Stack](https://img.shields.io/badge/backend-FastAPI-009688)
![Stack](https://img.shields.io/badge/frontend-React%2018%20%2B%20Vite-61dafb)
![Stack](https://img.shields.io/badge/styling-TailwindCSS-38bdf8)

## Features

- **Logistic Elo match model** with a 0–100 % "Elo Influence" slider — drag to
  0 % for coin-flip chaos, 100 % for a ratings-dominated tournament.
- **Full 2026 format** — 48 teams, 12 groups of 4, FIFA group tiebreakers
  (points → goal difference → goals scored), top 2 + 8 best third-placed teams
  into a 32-team single-elimination bracket.
- **Monte Carlo engine** — 1,000 runs in ~0.2 s; aggregates championship counts
  and how far each team advances.
- **Live WebSocket updates** — a progress bar and top-5 leaderboard update in
  real time (exactly 20 updates over a 1,000-run simulation).
- **ESPN-style bracket** — every knockout round, colour-coded by championship
  probability across five confidence levels, with percentage labels for the
  favourites.
- **Resilient** — bundled fallback Elo ratings if the external API is
  unavailable; WebSocket auto-reconnects; aborted runs still finish server-side
  and remain retrievable.

## Architecture

```
┌─────────────────┐     WebSocket /ws/simulate    ┌──────────────────┐
│  React Frontend │◄────────────────────────────►│  FastAPI Backend │
│  (Vite + Tailw.)│        HTTP /api/*            │                  │
│  Bracket · Slider│◄────────────────────────────►│  Sim Engine      │
│  Leaderboard · Bar│                              │  Tournament Logic│
└─────────────────┘                               │  Elo API Client  │
                                                   └────────┬─────────┘
                                                            ▼
                                                   ┌─────────────────┐
                                                   │  External Elo   │
                                                   │  API (optional) │
                                                   └─────────────────┘
```

## Project structure

```
World-Cup-2026-Sim/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app: REST + WebSocket
│   │   ├── models.py        # Pydantic models (API contract)
│   │   ├── probability.py   # Logistic Elo win probability + weight
│   │   ├── teams_data.py    # 48 teams, 12 groups, fallback Elo
│   │   ├── elo_client.py    # External Elo fetch + 60-min cache + fallback
│   │   ├── tournament.py    # Group stage + knockout bracket
│   │   ├── simulation.py    # Monte Carlo aggregation
│   │   └── session_store.py # In-memory session registry
│   └── tests/               # 41 tests (pytest)
├── frontend/
│   └── src/
│       ├── App.jsx          # Layout + orchestration
│       ├── useSimulation.js # WebSocket lifecycle hook
│       ├── api.js           # axios + ws helpers
│       ├── components/      # ControlPanel, Bracket, Leaderboard, …
│       └── utils/colors.js  # 5-level probability colour scale
└── docker-compose.yml       # Optional containerized dev
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (tested on 22)

## Local setup

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (optional) configure an external Elo API; works fully offline without it
cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` — interactive docs at
`http://localhost:8000/docs`.

### 2. Frontend (React + Vite)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/ws` to the backend on
port 8000, so there are no CORS issues in development.

### Run it

Adjust the **Elo Influence** slider, choose a run count (1,000 / 5,000 /
10,000), and click **Run Simulation**. Watch the progress bar and live
leaderboard, then explore the projected bracket and championship odds.

## Alternative: single-process / Docker

**Serve the built frontend from the backend** (one server, port 8000):

```bash
cd frontend && npm install && npm run build   # produces frontend/dist
cd ../backend && source .venv/bin/activate
uvicorn app.main:app --port 8000              # serves SPA + API at :8000
```

**Docker Compose** (frontend with hot reload on :5173, backend on :8000):

```bash
docker compose up --build
```

## API contract

| Method | Path | Description |
| --- | --- | --- |
| `GET`  | `/api/teams` | All 48 teams with cached Elo ratings |
| `POST` | `/api/simulate` | Body `{elo_weight, num_runs}` → `{session_id, ws_url}` |
| `GET`  | `/api/results/{session_id}` | Final aggregated results (or 202 while running) |
| `WS`   | `/ws/simulate?session_id=…` | Streams progress + final result |
| `GET`  | `/api/health` | Health + current Elo source |

**WebSocket progress message:**

```json
{
  "type": "progress",
  "runs_completed": 500,
  "total_runs": 1000,
  "top_5_teams": [{ "id": "ARG", "name": "Argentina", "wins": 138, "probability": 0.276 }]
}
```

OpenAPI/Swagger is auto-generated at `/docs` and `/openapi.json`.

## Configuration

`backend/.env` (see `backend/.env.example`):

| Variable | Purpose |
| --- | --- |
| `ELO_API_URL` | External Elo endpoint. If unset, bundled fallback ratings are used. |
| `ELO_API_KEY` | Optional API key (sent as `Authorization: Bearer` and `x-apisports-key`). |

The client accepts a flat `{"BRA": 2021, …}` map or a list of
`{"id"/"code"/"team": …, "elo"/"rating": …}` objects, with an optional
`{"response": […]}` wrapper. Ratings are cached for 60 minutes.

## Testing

```bash
cd backend && source .venv/bin/activate
pytest            # 41 tests: probability, tournament, Monte Carlo, Elo client, API
```

Coverage highlights: Elo-formula edge cases, group tiebreakers, exactly-32
qualifiers, bracket validity, championship-count invariants, the "20 progress
updates per 1,000 runs" guarantee, 0 %-weight ≈ uniform vs 100 %-weight
Elo-dominated, and the full WebSocket flow.

## Design notes

- **12 groups of 4 (not 16 × 3).** The brief's "16 groups of 3" conflicts with
  its own "groups A–L" and "top 2 + 8 best thirds = 32" rules. Only 12 groups of
  4 yield exactly 32 knockout qualifiers (2 × 12 + 8), which is also the real
  FIFA 2026 format, so that's what's implemented.
- **Group draw is representative.** Hosts (USA, Canada, Mexico) are seeded into
  separate groups; the rest is a plausible balanced draw. Swap assignments in
  `backend/app/teams_data.py` to match the official draw.
- **Knockout seeding.** The 32 qualifiers are seeded (winners → runners-up →
  best thirds, each ranked by FIFA criteria) into a standard balanced bracket
  (1 v 32, …) rather than FIFA's intricate third-place slotting table.
- **The displayed bracket is the "chalk" bracket** (favourites advance) for a
  stable layout; every cell is coloured by the team's Monte Carlo championship
  probability, so the colours shift with the slider even though the structure
  stays put.
- **Goal model.** Group scorelines come from a Poisson model whose supremacy
  scales with the *weighted* Elo gap (so tiebreakers behave sensibly); knockout
  ties are decided by a shootout drawn from the logistic win probability.

## License

MIT — for educational / demonstration use.
