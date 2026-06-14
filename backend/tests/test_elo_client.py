"""Tests for the Elo client: fallback, caching, and payload parsing."""
import pytest

from app.elo_client import EloClient, _parse_elo_payload


async def test_fallback_returns_48_teams_without_api():
    client = EloClient(api_url=None)
    teams = await client.get_teams()
    assert len(teams) == 48
    assert client.source == "fallback"
    # Bundled ratings are sensible.
    arg = next(t for t in teams if t.id == "ARG")
    assert 2000 < arg.elo_rating < 2300


async def test_cache_is_reused_within_ttl():
    client = EloClient(api_url=None)
    first = await client.get_teams()
    second = await client.get_teams()
    assert first is second  # same cached object, no reload


async def test_force_refresh_reloads():
    client = EloClient(api_url=None)
    first = await client.get_teams()
    second = await client.get_teams(force_refresh=True)
    assert first is not second
    assert [t.id for t in first] == [t.id for t in second]


async def test_expired_cache_reloads(monkeypatch):
    client = EloClient(api_url=None, ttl_seconds=0)
    first = await client.get_teams()
    second = await client.get_teams()
    assert first is not second  # TTL of 0 -> always reloads


async def test_api_ratings_are_applied(monkeypatch):
    client = EloClient(api_url="https://example.test/elo")

    async def fake_fetch():
        return {"ARG": 2500, "BRA": 2400}

    monkeypatch.setattr(client, "_fetch_elo_map", fake_fetch)
    teams = await client.get_teams()
    assert client.source == "api"
    by_id = {t.id: t for t in teams}
    assert by_id["ARG"].elo_rating == 2500
    assert by_id["BRA"].elo_rating == 2400
    # Untouched teams keep their bundled rating.
    assert by_id["MEX"].elo_rating == 1790


async def test_api_failure_falls_back(monkeypatch):
    client = EloClient(api_url="https://example.test/elo")

    async def boom():
        raise RuntimeError("network down")

    monkeypatch.setattr(client, "_fetch_elo_map", boom)
    teams = await client.get_teams()
    assert client.source == "fallback"
    assert len(teams) == 48


def test_parse_flat_map():
    assert _parse_elo_payload({"BRA": 2021, "ARG": 2143}) == {
        "BRA": 2021.0,
        "ARG": 2143.0,
    }


def test_parse_list_of_objects():
    payload = [
        {"code": "BRA", "elo": 2021},
        {"id": "ARG", "rating": 2143},
        {"team": "fra", "elo_rating": 2081},
    ]
    parsed = _parse_elo_payload(payload)
    assert parsed == {"BRA": 2021.0, "ARG": 2143.0, "FRA": 2081.0}


def test_parse_response_wrapper():
    payload = {"response": [{"code": "ESP", "elo": 2051}]}
    assert _parse_elo_payload(payload) == {"ESP": 2051.0}
