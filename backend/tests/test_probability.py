"""Tests for the Elo win-probability model and the weight knob."""
import math

import pytest

from app.probability import (
    elo_win_probability,
    normalize_weight,
    weighted_win_probability,
)


def test_equal_ratings_is_coin_flip():
    assert elo_win_probability(1900, 1900) == pytest.approx(0.5)


def test_400_point_edge_matches_known_value():
    # A 400-point advantage corresponds to ~10:1 odds (0.909...).
    assert elo_win_probability(2000, 1600) == pytest.approx(10 / 11, abs=1e-6)
    assert elo_win_probability(1600, 2000) == pytest.approx(1 / 11, abs=1e-6)


def test_probabilities_are_symmetric():
    for home, away in [(2100, 1800), (1750, 1900), (2000, 2000)]:
        assert elo_win_probability(home, away) + elo_win_probability(
            away, home
        ) == pytest.approx(1.0)


def test_probability_bounds():
    assert 0.0 < elo_win_probability(2200, 1500) < 1.0
    assert elo_win_probability(3000, 1000) > 0.99


def test_weight_zero_is_always_half():
    for home, away in [(2143, 1503), (1800, 2100), (1900, 1900)]:
        assert weighted_win_probability(home, away, 0.0) == pytest.approx(0.5)


def test_weight_one_equals_raw_elo():
    assert weighted_win_probability(2000, 1600, 1.0) == pytest.approx(
        elo_win_probability(2000, 1600)
    )


def test_weight_half_is_midpoint():
    raw = elo_win_probability(2000, 1600)
    expected = 0.5 + 0.5 * (raw - 0.5)
    assert weighted_win_probability(2000, 1600, 0.5) == pytest.approx(expected)


def test_weight_is_clamped():
    assert weighted_win_probability(2000, 1600, 5.0) == pytest.approx(
        elo_win_probability(2000, 1600)
    )
    assert weighted_win_probability(2000, 1600, -3.0) == pytest.approx(0.5)


def test_normalize_weight():
    assert normalize_weight(0) == 0.0
    assert normalize_weight(50) == 0.5
    assert normalize_weight(100) == 1.0
    assert normalize_weight(150) == 1.0  # clamped
    assert normalize_weight(-10) == 0.0  # clamped


def test_weight_monotonic_in_favorite_direction():
    # Increasing weight should push the favorite's probability further from 0.5.
    probs = [weighted_win_probability(2100, 1700, w / 10) for w in range(11)]
    assert all(math.isclose(b - a, probs[1] - probs[0]) or b >= a for a, b in zip(probs, probs[1:]))
    assert probs[0] == pytest.approx(0.5)
    assert probs[-1] > probs[0]
