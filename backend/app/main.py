"""FastAPI application: REST + WebSocket API for the World Cup 2026 simulator.

Endpoints (the v1 API contract):
  * GET  /api/teams                -> 48 teams with cached Elo ratings
  * POST /api/simulate             -> create a session, return its WebSocket URL
  * GET  /api/results/{session_id} -> final aggregated results for a session
  * WS   /ws/simulate              -> stream live progress + final result

The CPU-bound Monte Carlo loop runs in a worker thread (``asyncio.to_thread``)
while progress messages are bridged back to the event loop through an
``asyncio.Queue`` and streamed to the client. If the client disconnects
mid-run (the "abort" button), the simulation keeps running in the background and
its result is still retrievable via GET /api/results.
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .elo_client import EloClient
from .models import (
    SimulateRequest,
    SimulateResponse,
    SimulationProgress,
    Team,
)
from .probability import normalize_weight
from .session_store import SessionStore
from .simulation import run_simulation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worldcup.main")

elo_client = EloClient()
store = SessionStore()

# Keep references to background simulation tasks so they aren't garbage
# collected if the client disconnects before completion.
_background_tasks: set[asyncio.Task] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the Elo cache on startup so /api/teams is instant."""
    teams = await elo_client.get_teams()
    logger.info("Loaded %d teams (source=%s) on startup.", len(teams), elo_client.source)
    yield


app = FastAPI(
    title="World Cup 2026 Simulator",
    description="Monte Carlo tournament simulator with live WebSocket progress.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for local frontend dev (Vite default ports + wildcard fallback).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "elo_source": elo_client.source}


@app.get("/api/teams", response_model=list[Team])
async def get_teams() -> list[Team]:
    """Return all 48 teams with their (cached) Elo ratings."""
    return await elo_client.get_teams()


@app.post("/api/simulate", response_model=SimulateResponse)
async def start_simulation(req: SimulateRequest) -> SimulateResponse:
    """Create a simulation session and return the WebSocket URL to drive it."""
    session_id = uuid4().hex
    store.create(session_id, req.elo_weight, req.num_runs)
    ws_url = f"/ws/simulate?session_id={session_id}"
    return SimulateResponse(
        session_id=session_id,
        ws_url=ws_url,
        elo_weight=req.elo_weight,
        num_runs=req.num_runs,
    )


@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """Return final results for a session, or its current status."""
    session = store.get(session_id)
    if session is None:
        return JSONResponse(status_code=404, content={"detail": "Unknown session"})
    if session.status == "complete" and session.result is not None:
        return session.result
    if session.status == "error":
        return JSONResponse(
            status_code=500, content={"detail": session.error or "Simulation error"}
        )
    # pending / running
    return JSONResponse(
        status_code=202,
        content={"detail": "Simulation in progress", "status": session.status},
    )


@app.websocket("/ws/simulate")
async def ws_simulate(websocket: WebSocket) -> None:
    """Stream simulation progress and the final result over a WebSocket.

    The client may either (a) POST /api/simulate first and connect with
    ``?session_id=...``, or (b) connect directly and send an initial JSON
    message ``{elo_weight, num_runs}``.
    """
    await websocket.accept()

    session_id = websocket.query_params.get("session_id")
    session = store.get(session_id) if session_id else None

    if session is None:
        # No pre-created session: read params from the first client message.
        try:
            init = await websocket.receive_json()
        except Exception:
            await websocket.close(code=1003)
            return
        elo_weight = float(init.get("elo_weight", 100.0))
        num_runs = int(init.get("num_runs", 1000))
        session_id = session_id or uuid4().hex
        session = store.create(session_id, elo_weight, num_runs)

    # If the session already finished (e.g. a client reconnecting after the run
    # completed), just replay the final result and close.
    if session.status == "complete" and session.result is not None:
        await websocket.send_json(session.result.model_dump())
        await websocket.close()
        return

    # Atomically claim the run. If another connection already owns it (a
    # reconnect mid-run), wait for that run to finish instead of starting a
    # second simulation.
    if not store.begin_run(session.session_id):
        await _wait_and_send_result(websocket, session.session_id)
        return

    weight = normalize_weight(session.elo_weight)
    teams = await elo_client.get_teams()

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def on_progress(runs_completed: int, total: int, top5) -> None:
        # Runs in the worker thread -> hand the message back to the loop.
        msg = SimulationProgress(
            runs_completed=runs_completed, total_runs=total, top_5_teams=top5
        ).model_dump()
        loop.call_soon_threadsafe(queue.put_nowait, ("progress", msg))

    def should_stop() -> bool:
        s = store.get(session.session_id)
        return bool(s and s.stop_requested)

    async def worker() -> None:
        try:
            result = await asyncio.to_thread(
                run_simulation,
                teams,
                weight,
                session.num_runs,
                session.session_id,
                on_progress,
                50,
                None,
                should_stop,
            )
            store.set_result(session.session_id, result)
            loop.call_soon_threadsafe(
                queue.put_nowait, ("complete", result.model_dump())
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Simulation failed")
            store.set_error(session.session_id, str(exc))
            loop.call_soon_threadsafe(
                queue.put_nowait, ("error", {"type": "error", "message": str(exc)})
            )

    task = asyncio.create_task(worker())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    try:
        while True:
            kind, payload = await queue.get()
            await websocket.send_json(payload)
            if kind in ("complete", "error"):
                break
        await websocket.close()
    except (WebSocketDisconnect, RuntimeError):
        # Client aborted/closed. Per the spec the simulation continues in the
        # background; its result remains available via GET /api/results.
        logger.info("WebSocket client disconnected; simulation continues in background.")


async def _wait_and_send_result(websocket: WebSocket, session_id: str) -> None:
    """Wait for an in-flight run to finish, then send its result.

    Used when a client (re)connects to a session that is already running, so we
    never start a duplicate simulation. Polls the store until the result is
    available or an error occurs.
    """
    try:
        for _ in range(6000):  # up to ~10 minutes at 0.1s cadence
            session = store.get(session_id)
            if session is None:
                await websocket.close(code=1011)
                return
            if session.status == "complete" and session.result is not None:
                await websocket.send_json(session.result.model_dump())
                await websocket.close()
                return
            if session.status == "error":
                await websocket.send_json(
                    {"type": "error", "message": session.error or "Simulation error"}
                )
                await websocket.close()
                return
            await asyncio.sleep(0.1)
        await websocket.close(code=1013)  # try again later
    except (WebSocketDisconnect, RuntimeError):
        return


# Optionally serve the built frontend (frontend/dist) when present, so the whole
# app can run from a single process in production-like setups.
_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(_DIST_DIR):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_DIST_DIR, html=True), name="static")
