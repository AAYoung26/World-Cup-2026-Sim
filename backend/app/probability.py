"""Match win-probability model.

Implements the standard logistic Elo formula with a user-controllable weight
that blends between a pure Elo prediction (weight = 1.0) and a coin-flip
(weight = 0.0). This is the knob exposed by the frontend "Elo Influence" slider.
"""
from __future__ import annotations


def elo_win_probability(elo_home: float, elo_away: float) -> float:
    """Probability that the home team beats the away team using pure Elo.

    Standard logistic formula:
        P(home wins) = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))

    Equal ratings -> 0.5. A 400-point edge -> ~0.91.
    """
    return 1.0 / (1.0 + 10.0 ** ((elo_away - elo_home) / 400.0))


def weighted_win_probability(
    elo_home: float, elo_away: float, weight: float
) -> float:
    """Blend the Elo prediction toward 0.5 by ``weight``.

    Args:
        elo_home: Home team Elo rating.
        elo_away: Away team Elo rating.
        weight: Elo influence in [0.0, 1.0]. 1.0 = full Elo, 0.0 = 50/50.
            Values are clamped to the valid range.

    Returns:
        A probability in [0.0, 1.0]. With ``weight`` = 0 the result is always
        0.5 (uniform random outcomes); with ``weight`` = 1 it is the raw Elo
        probability. Intermediate values linearly interpolate, so the slider has
        a smooth, intuitive effect on how much ratings matter.
    """
    w = _clamp01(weight)
    base = elo_win_probability(elo_home, elo_away)
    return 0.5 + w * (base - 0.5)


def normalize_weight(slider_value: float) -> float:
    """Convert a 0-100 slider value into a 0.0-1.0 weight."""
    return _clamp01(slider_value / 100.0)


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
