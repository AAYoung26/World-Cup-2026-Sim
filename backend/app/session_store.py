"""In-memory store for simulation sessions.

A session is created by ``POST /api/simulate`` and is driven to completion by
the WebSocket handler. Results live in process memory for the life of the
server (no database in v1). Access happens from the asyncio event loop, so a
plain dict guarded by a lock is sufficient.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional

from .models import SimulationResult


@dataclass
class Session:
    """One simulation session and its lifecycle state."""

    session_id: str
    elo_weight: float          # 0-100 slider value
    num_runs: int
    status: str = "pending"    # pending -> running -> complete | aborted | error
    result: Optional[SimulationResult] = None
    error: Optional[str] = None
    stop_requested: bool = field(default=False)


class SessionStore:
    """Thread-safe registry of simulation sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, session_id: str, elo_weight: float, num_runs: int) -> Session:
        session = Session(
            session_id=session_id, elo_weight=elo_weight, num_runs=num_runs
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(session_id)

    def begin_run(self, session_id: str) -> bool:
        """Atomically claim a pending session for execution.

        Returns True if the caller should run the simulation, or False if the
        session is already running/complete (so a reconnecting client should
        instead wait for the existing run's result rather than double-running).
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.status in ("running", "complete"):
                return False
            session.status = "running"
            return True

    def set_status(self, session_id: str, status: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = status

    def set_result(self, session_id: str, result: SimulationResult) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].result = result
                self._sessions[session_id].status = "complete"

    def set_error(self, session_id: str, message: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = "error"
                self._sessions[session_id].error = message

    def request_stop(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].stop_requested = True
