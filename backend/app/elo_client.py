"""External Elo-rating client with in-memory caching and graceful fallback.

The build brief calls for fetching national-team Elo ratings from a public API
(API-Football / EloRatings.net) and caching them for 60 minutes. Those services
either require an API key or do not expose a clean JSON endpoint, so this client
is structured defensively:

* If ``ELO_API_URL`` is configured it attempts a real fetch and overlays the
  returned ratings onto our fixed group structure.
* On any failure -- no URL, network error, bad payload -- it falls back to the
  bundled ratings in :mod:`teams_data` so the simulator always has 48 rated
  teams.

Group assignments always come from our hard-coded draw; only the Elo numbers are
refreshed from the API, since the external services don't publish 2026 groups.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx

from .models import Team
from .teams_data import default_teams

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60 * 60  # 60-minute cache per the spec.


class EloClient:
    """Fetches and caches team Elo ratings."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ) -> None:
        self.api_url = api_url if api_url is not None else os.getenv("ELO_API_URL")
        self.api_key = api_key if api_key is not None else os.getenv("ELO_API_KEY")
        self.ttl_seconds = ttl_seconds
        self._cache: Optional[list[Team]] = None
        self._cached_at: float = 0.0
        self._source: str = "uninitialized"

    @property
    def source(self) -> str:
        """Where the currently cached data came from ('api' or 'fallback')."""
        return self._source

    def _cache_valid(self) -> bool:
        return (
            self._cache is not None
            and (time.monotonic() - self._cached_at) < self.ttl_seconds
        )

    async def get_teams(self, force_refresh: bool = False) -> list[Team]:
        """Return 48 teams with Elo ratings, using the cache when fresh."""
        if not force_refresh and self._cache_valid():
            return self._cache  # type: ignore[return-value]

        teams = await self._load_teams()
        self._cache = teams
        self._cached_at = time.monotonic()
        return teams

    async def _load_teams(self) -> list[Team]:
        base_teams = default_teams()
        if not self.api_url:
            logger.info("No ELO_API_URL configured; using bundled Elo ratings.")
            self._source = "fallback"
            return base_teams

        try:
            elo_map = await self._fetch_elo_map()
            if not elo_map:
                raise ValueError("empty Elo payload")
            applied = 0
            for team in base_teams:
                if team.id in elo_map:
                    team.elo_rating = int(round(elo_map[team.id]))
                    applied += 1
            logger.info("Loaded Elo from API for %d/%d teams.", applied, len(base_teams))
            self._source = "api" if applied else "fallback"
            return base_teams
        except Exception as exc:  # noqa: BLE001 - fall back on any failure
            logger.warning("Elo API fetch failed (%s); using bundled ratings.", exc)
            self._source = "fallback"
            return base_teams

    async def _fetch_elo_map(self) -> dict[str, float]:
        """Fetch a {team_id: elo} map from the configured API.

        Accepts a couple of common shapes so it can adapt to different
        providers without code changes:
          * ``{"BRA": 2021, "ARG": 2143, ...}``
          * ``[{"id"|"code"|"team": "BRA", "elo"|"rating": 2021}, ...]``
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["x-apisports-key"] = self.api_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.api_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return _parse_elo_payload(data)


def _parse_elo_payload(data: object) -> dict[str, float]:
    """Best-effort parse of a few common Elo JSON shapes into {id: elo}."""
    elo_map: dict[str, float] = {}
    if isinstance(data, dict):
        # Either a flat {code: elo} map or {"response": [...]}.
        if "response" in data and isinstance(data["response"], list):
            return _parse_elo_payload(data["response"])
        for key, value in data.items():
            if isinstance(value, (int, float)):
                elo_map[str(key).upper()] = float(value)
    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            tid = item.get("id") or item.get("code") or item.get("team")
            elo = item.get("elo") or item.get("rating") or item.get("elo_rating")
            if tid is not None and elo is not None:
                elo_map[str(tid).upper()] = float(elo)
    return elo_map
