"""Tests for the tournament engine: groups, seeding, and the knockout bracket."""
from random import Random

from app.models import Stage
from app.teams_data import GROUPS, default_teams
from app.tournament import (
    _seed_bracket_order,
    runtime_groups,
    simulate_group,
    simulate_tournament,
)


def _groups():
    return runtime_groups(default_teams())


def test_there_are_12_groups_of_4():
    groups = _groups()
    assert len(groups) == 12
    assert sorted(groups.keys()) == GROUPS
    for letter, teams in groups.items():
        assert len(teams) == 4, f"group {letter} should have 4 teams"


def test_group_standings_are_ranked_and_consistent():
    groups = _groups()
    rng = Random(42)
    standings = simulate_group(groups["D"], 1.0, rng)
    assert len(standings) == 4
    # Sorted best-to-worst by (points, gd, gf, elo).
    keys = [(s.points, s.gd, s.gf, s.team.elo) for s in standings]
    assert keys == sorted(keys, reverse=True)
    # 6 matches distribute between 12 (all draws) and 18 (no draws) points.
    total_points = sum(s.points for s in standings)
    assert 12 <= total_points <= 18


def test_seed_bracket_order_is_balanced_permutation():
    order = _seed_bracket_order(32)
    assert sorted(order) == list(range(1, 33))
    # First-round pairs (consecutive) must each sum to 33 (1v32, 2v31, ...).
    for i in range(0, 32, 2):
        assert order[i] + order[i + 1] == 33


def test_simulate_tournament_produces_one_champion():
    groups = _groups()
    rng = Random(7)
    outcome = simulate_tournament(groups, 1.0, rng)
    all_ids = {t.id for g in groups.values() for t in g}
    assert outcome.champion.id in all_ids
    assert outcome.furthest_stage[outcome.champion.id] == Stage.WINNER


def test_exactly_32_teams_reach_knockout():
    groups = _groups()
    rng = Random(11)
    outcome = simulate_tournament(groups, 1.0, rng)
    knockout = [
        tid
        for tid, stage in outcome.furthest_stage.items()
        if stage != Stage.GROUP
    ]
    assert len(knockout) == 32


def test_deterministic_mode_strongest_team_wins():
    # With chalk (no randomness) the highest-Elo team must win the whole thing.
    groups = _groups()
    strongest = max(
        (t for g in groups.values() for t in g), key=lambda t: t.elo
    )
    outcome = simulate_tournament(groups, 1.0, Random(0), deterministic=True)
    assert outcome.champion.id == strongest.id  # Argentina in the bundled data.


def test_recorded_bracket_has_expected_round_sizes():
    groups = _groups()
    outcome = simulate_tournament(
        groups, 1.0, Random(0), deterministic=True, record_bracket=True
    )
    assert outcome.bracket_rounds is not None
    expected = {
        "ROUND_OF_32": 16,
        "ROUND_OF_16": 8,
        "QUARTER": 4,
        "SEMI": 2,
        "FINAL": 1,
    }
    for stage, count in expected.items():
        assert len(outcome.bracket_rounds[stage]) == count


def test_zero_weight_group_is_symmetric_over_many_runs():
    # With weight 0, no team should systematically dominate its group.
    groups = _groups()
    wins = {t.id: 0 for t in groups["D"]}
    for s in range(400):
        standings = simulate_group(groups["D"], 0.0, Random(s))
        wins[standings[0].team.id] += 1
    # The strongest team should not win the group dramatically more often than
    # a uniform 1/4 share would suggest.
    top_share = max(wins.values()) / 400
    assert top_share < 0.45
